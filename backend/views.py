import datetime

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View
from rest_framework import serializers

from backend.core.models import Attachments, Equipment, Exercises, Workouts
from backend.core.serializers import WorkoutSerializer


def homepageView(request):
    return render(request, "homepage.html")


class WorkoutFormView(View):
    template_name = "core/workout_form.html"

    def get_context_data(self, request):
        """Get context data with available options"""
        last_workout = Workouts.objects.filter(user=request.user).order_by("-ta_created_at").first()
        if last_workout:
            default_workout_number = last_workout.workout_number
            # Next set for same (workout, exercise); reset to 1 when user changes exercise or workout
            default_set_number = min(last_workout.set_number + 1, 200)
            last_exercise_name = last_workout.exercise.exercise_name
        else:
            default_workout_number = 1
            default_set_number = 1
            last_exercise_name = ""

        return {
            "exercises": Exercises.objects.all().order_by("exercise_name"),
            "attachments": Attachments.objects.all().order_by("attachment_name"),
            "equipment": Equipment.objects.all().order_by("equipment_name"),
            "today_date": datetime.date.today().isoformat(),
            "default_workout_number": default_workout_number,
            "default_set_number": default_set_number,
            "last_exercise_name": last_exercise_name,
        }

    def get(self, request):
        storage = messages.get_messages(request)
        storage.used = True
        context = self.get_context_data(request)
        # Restore form data from session (validation errors) or prefill (success: keep fields, reset set/reps/load)
        if "workout_form_data" in request.session:
            context["form_data"] = request.session.pop("workout_form_data")
        elif "workout_form_prefill" in request.session:
            prefill = request.session.pop("workout_form_prefill")
            default_set = context["default_set_number"]
            # Template expects list values (form_data.field.0)
            context["form_data"] = {
                "workout_number": [str(prefill["workout_number"])],
                "exercise_name": [prefill["exercise_name"]],
                "attachment_name": [prefill["attachment_name"]],
                "equipment_name": [prefill["equipment_name"]],
                "workout_split": [prefill["workout_split"]],
                "date": [prefill["date"] or context["today_date"]],
                "set_type": [prefill["set_type"]],
                "unit": [prefill["unit"]],
                "comments": [prefill["comments"]],
                "set_number": [str(default_set)],
                "repetitions": ["0"],
                "load": ["0"],
            }
        else:
            context["form_data"] = {}
        return render(request, self.template_name, context)

    def post(self, request):
        # Check if this is a delete request
        if "delete_last" in request.POST:
            # Delete the most recent workout for this user
            last_workout = Workouts.objects.filter(user=request.user).order_by("-ta_created_at").first()
            if last_workout:
                workout_info = f"{last_workout.exercise.exercise_name} - Set {last_workout.set_number} - {last_workout.repetitions} reps @ {last_workout.load}{last_workout.unit} on {last_workout.date.date_id}"
                last_workout.delete()
                messages.success(request, f"Deleted: {workout_info}")
            else:
                messages.error(request, "No workouts found to delete.")
            return redirect("workout-logger")

        # Normal form submission
        serializer = WorkoutSerializer(data=request.POST, context={"request": request})

        if not serializer.is_valid():
            # Validation failed - show errors
            for field, error_list in serializer.errors.items():
                for error in error_list:
                    messages.error(request, f"{field}: {error}")
            # Store form data in session and redirect (Post-Redirect-Get pattern)
            # so that when reloading, the form with errors isn't resubmitted but is cleared
            request.session["workout_form_data"] = dict(request.POST)
            return redirect("workout-logger")

        # Validation passed, try to save
        try:
            submitted_set_number = request.POST.get("set_number")
            serializer.save()
            v = serializer.validated_data
            actual_set_number = v.get("set_number")
            if submitted_set_number is not None and str(actual_set_number) != str(submitted_set_number):
                messages.success(
                    request,
                    f"Workout submitted successfully! Set number was set to {actual_set_number} for this exercise in this workout.",
                )
            else:
                messages.success(request, "Workout submitted successfully!")
            # Keep most fields for next load; only set_number, repetitions, load will be reset
            date_val = v.get("date")
            if hasattr(date_val, "isoformat"):
                date_val = date_val.isoformat()
            request.session["workout_form_prefill"] = {
                "workout_number": v.get("workout_number"),
                "exercise_name": v.get("exercise_name"),
                "attachment_name": v.get("attachment_name") or "",
                "equipment_name": v.get("equipment_name") or "",
                "workout_split": v.get("workout_split") or "",
                "date": date_val,
                "set_type": v.get("set_type") or "Working set",
                "unit": v.get("unit") or "KG",
                "comments": v.get("comments") or "",
            }
            return redirect("workout-logger")
        except serializers.ValidationError as e:
            # Handle validation errors from create() method
            if hasattr(e, "detail"):
                # Extract message from ErrorDetail or list
                if isinstance(e.detail, list):
                    error_msg = ", ".join([str(item) for item in e.detail])
                elif hasattr(e.detail, "string"):
                    error_msg = e.detail.string
                else:
                    error_msg = str(e.detail)
            else:
                error_msg = str(e)
            messages.error(request, error_msg)
            request.session["workout_form_data"] = dict(request.POST)
            return redirect("workout-logger")
        except Exception as e:
            messages.error(request, f"Error saving workout: {str(e)}")
            request.session["workout_form_data"] = dict(request.POST)
            return redirect("workout-logger")
