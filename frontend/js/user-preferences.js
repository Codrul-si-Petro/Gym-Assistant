const UNIT_KEY = "preferred_unit";

export function getPreferredUnit() {
  const value = localStorage.getItem(UNIT_KEY);
  return value === "LBS" ? "LBS" : "KG";
}

export function setPreferredUnit(unit) {
  const normalized = unit === "LBS" ? "LBS" : "KG";
  localStorage.setItem(UNIT_KEY, normalized);
  return normalized;
}

export function convertKgToPreferred(kgValue, unit = getPreferredUnit()) {
  const kg = Number(kgValue) || 0;
  if (unit === "LBS") return kg * 2.2046226218;
  return kg;
}

export function unitSuffix(unit = getPreferredUnit()) {
  return unit === "LBS" ? "lbs" : "kg";
}
