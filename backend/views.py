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

    def get_context_data(self):
        """Get context data with available options"""
        return {
            "exercises": Exercises.objects.all().order_by("exercise_name"),
            "attachments": Attachments.objects.all().order_by("attachment_name"),
            "equipment": Equipment.objects.all().order_by("equipment_name"),
            "today_date": datetime.date.today().isoformat(),
        }

    def get(self, request):
        storage = messages.get_messages(request)
        storage.used = True
        context = self.get_context_data()
        # Restore form data from session if it exists (from previous POST with errors)
        if "workout_form_data" in request.session:
            context["form_data"] = request.session.pop("workout_form_data")
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
            serializer.save()
            messages.success(request, "Workout submitted successfully!")
            # Redirect on success to clear form data
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
