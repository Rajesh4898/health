"""AI Diet Planner — calorie estimation and sample meal generation."""

import math

ACTIVITY_FACTOR = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
}

GOAL_ADJUST = {
    "maintain": (0, 0, "Weight maintenance"),
    "lose": (-0.1, 0.8, "Gradual weight loss"),
    "gain": (0.1, 1.15, "Gradual weight gain"),
    "wellness": (0, 0, "General wellness"),
}

MACRO_RATIOS = {
    "maintain": (0.30, 0.45, 0.25),
    "lose": (0.35, 0.40, 0.25),
    "gain": (0.25, 0.45, 0.30),
    "wellness": (0.30, 0.45, 0.25),
}


def compute_metrics(age, sex, height_cm, weight_kg, activity, goal):
    """Return dict with BMR, TDEE, goal calories and macros."""
    sex = (sex or "female").lower()
    if sex in ("male", "m"):
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    activity = activity or "sedentary"
    factor = ACTIVITY_FACTOR.get(activity, 1.2)
    tdee = bmr * factor

    adj_pct, prot_mult, goal_label = GOAL_ADJUST.get(goal, (0, 1.0, "General wellness"))
    goal_cal = tdee * (1 + adj_pct)
    goal_cal = round(goal_cal / 10) * 10

    p_ratio, c_ratio, f_ratio = MACRO_RATIOS.get(goal, (0.30, 0.45, 0.25))

    protein_g = round((goal_cal * p_ratio) / 4)
    carbs_g = round((goal_cal * c_ratio) / 4)
    fat_g = round((goal_cal * f_ratio) / 9)

    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "goal_calories": goal_cal,
        "goal_label": goal_label,
        "protein_g": protein_g,
        "carbs_g": carbs_g,
        "fat_g": fat_g,
        "protein_cal": round(goal_cal * p_ratio),
        "carbs_cal": round(goal_cal * c_ratio),
        "fat_cal": round(goal_cal * f_ratio),
    }


def _is_glucose_high(analysis):
    for item in analysis or []:
        if item["key"] in ("glucose", "fasting glucose", "hba1c") and item["status"] in ("HIGH", "BORDERLINE"):
            return True
    return False


def _is_lipid_high(analysis):
    for item in analysis or []:
        if item["key"] in ("ldl", "total cholesterol", "triglycerides") and item["status"] in ("HIGH", "BORDERLINE"):
            return True
    return False


def _is_vitd_low(analysis):
    for item in analysis or []:
        if item["key"] == "vitamin d" and item["status"] in ("LOW", "BORDERLINE"):
            return True
    return False


def _health_notes(analysis):
    """Produce generic food guidance adapted to report findings."""
    notes = []
    if _is_glucose_high(analysis):
        notes.append("Prefer high-fiber foods, moderate refined carbohydrates and avoid sugary beverages (based on your report showing elevated glucose/HbA1c).")
    if _is_lipid_high(analysis):
        notes.append("Favor fiber-rich foods, whole grains, vegetables/fruits and moderate foods high in saturated/trans fats (report shows elevated cholesterol/LDL).")
    if _is_vitd_low(analysis):
        notes.append("Your report shows low Vitamin D; discuss appropriate management with a clinician (we do not prescribe supplements or doses).")
    if not notes:
        notes.append("No specific dietary flags from your latest report. This plan is general wellness guidance.")
    return notes


# Simple food database: (name, protein g, carbs g, fat g, cal)
FOODS = {
    "vegetarian": {
        "breakfast": [
            ("Oats with milk & berries", 12, 45, 8, 300),
            ("Whole-wheat toast with peanut butter & banana", 14, 50, 12, 380),
            ("Veggie omelette with 2 eggs & whole-wheat toast", 20, 35, 16, 380),
        ],
        "snack_m": [
            ("Apple with a handful of almonds", 6, 22, 8, 180),
            ("Greek yogurt with honey", 14, 15, 3, 150),
            ("Mixed fruit bowl", 3, 35, 1, 150),
        ],
        "lunch": [
            ("Dal, rice/brown rice, green salad & curd", 18, 70, 10, 450),
            ("Chickpea & vegetable stir-fry with roti", 20, 65, 12, 460),
            ("Vegetable khichdi with yogurt salad", 16, 70, 8, 420),
        ],
        "snack_e": [
            ("Roasted makhana (fox nuts)", 8, 20, 2, 130),
            ("Hummus with veggie sticks", 6, 20, 6, 160),
            ("Peanut butter rice cakes", 5, 22, 6, 170),
        ],
        "dinner": [
            ("Tofu/soy stir-fry with brown rice & steamed greens", 24, 60, 14, 460),
            ("Paneer veggie curry with roti", 22, 60, 16, 480),
            ("Vegetable pulao with curd & salad", 12, 70, 9, 420),
        ],
    },
    "nonvegetarian": {
        "breakfast": [
            ("Egg white omelette with whole-wheat toast", 24, 35, 10, 330),
            ("Egg scramble with vegetables & milk", 22, 22, 15, 340),
            ("Oats with milk, banana & almonds", 15, 45, 8, 320),
        ],
        "snack_m": [
            ("Boiled egg with a small fruit", 12, 15, 6, 140),
            ("Greek yogurt with berries", 14, 15, 3, 150),
            ("Veggie & chicken strip roll (whole wheat)", 16, 25, 9, 240),
        ],
        "lunch": [
            ("Grilled chicken, brown rice & salad", 35, 55, 14, 500),
            ("Fish curry with vegetables & whole-wheat roti", 30, 50, 16, 490),
            ("Chicken & vegetable stir-fry with rice", 33, 55, 13, 470),
        ],
        "snack_e": [
            ("Grilled chicken strips", 30, 2, 4, 170),
            ("Roasted makhanas", 8, 20, 2, 130),
            ("Cottage cheese (paneer) cubes with mint", 15, 4, 10, 170),
        ],
        "dinner": [
            ("Grilled fish with steamed vegetables", 34, 18, 14, 350),
            ("Chicken curry with roti & salad", 32, 45, 14, 440),
            ("Chicken & vegetable soup with whole-wheat bread", 28, 40, 10, 370),
        ],
    },
}

MEAL_NAMES = {
    "breakfast": "Breakfast",
    "snack_m": "Morning Snack",
    "lunch": "Lunch",
    "snack_e": "Evening Snack",
    "dinner": "Dinner",
}


def _pick_food(food_list, allergies, idx):
    """Choose a food item respecting allergies (best effort)."""
    allergy_lower = [a.strip().lower() for a in (allergies or []) if a.strip()]
    candidates = food_list
    if allergy_lower:
        filtered = []
        for item in candidates:
            lowered = ", ".join(str(part) for part in item).lower()
            if not any(a in lowered for a in allergy_lower):
                filtered.append(item)
        if filtered:
            candidates = filtered
    return candidates[idx % len(candidates)]


def generate_plan(age, sex, height_cm, weight_kg, activity, diet_type, goal, allergies, analysis):
    """Generate full sample diet plan."""
    metrics = compute_metrics(age, sex, height_cm, weight_kg, activity, goal)
    diet_type = (diet_type or "vegetarian").lower()
    if diet_type not in ("vegetarian", "nonvegetarian"):
        diet_type = "vegetarian"
    db = FOODS[diet_type]

    # Deterministic rotation seed
    seed = int(round(weight_kg * 3 + height_cm))
    plan = []
    total_cal = 0
    total_p = total_c = total_f = 0

    for i, key in enumerate(["breakfast", "snack_m", "lunch", "snack_e", "dinner"]):
        name, p, c, f, cal = _pick_food(db[key], allergies, (seed + i) % len(db[key]))
        total_cal += cal
        total_p += p
        total_c += c
        total_f += f
        plan.append({
            "meal": MEAL_NAMES[key],
            "foods": name,
            "calories": cal,
            "protein": p,
            "carbs": c,
            "fats": f,
        })

    notes = _health_notes(analysis)
    return {
        "metrics": metrics,
        "meals": plan,
        "totals": {
            "calories": total_cal,
            "protein": total_p,
            "carbs": total_c,
            "fats": total_f,
        },
        "notes": notes,
        "disclaimer": "SAMPLE GENERAL WELLNESS PLAN — educational only, not a medical prescription. "
                      "Adapt portion sizes and confirm with your healthcare professional.",
    }


def validate_diet_form(form):
    """Return (errors, cleaned_kwargs)."""
    errors = {}
    try:
        age = int(form.get("age", ""))
        if not 10 <= age <= 100:
            errors["age"] = "Please enter a valid age (10–100)."
    except (TypeError, ValueError):
        errors["age"] = "Please enter a valid age."
        age = None

    sex = (form.get("sex") or "").strip().lower()
    if sex not in ("male", "female"):
        errors["sex"] = "Please select biological sex."

    try:
        height = float(form.get("height", "").replace(",", "."))
        if not 100 <= height <= 250:
            errors["height"] = "Height should be 100–250 cm."
    except (TypeError, ValueError):
        errors["height"] = "Please enter a valid height in cm."
        height = None

    try:
        weight = float(form.get("weight", "").replace(",", "."))
        if not 30 <= weight <= 250:
            errors["weight"] = "Weight should be 30–250 kg."
    except (TypeError, ValueError):
        errors["weight"] = "Please enter a valid weight in kg."
        weight = None

    activity = (form.get("activity") or "").strip()
    if activity not in ACTIVITY_FACTOR:
        errors["activity"] = "Please select an activity level."

    diet_type = (form.get("diet") or "").strip().lower()
    if diet_type not in ("vegetarian", "nonvegetarian"):
        errors["diet"] = "Please select vegetarian or non-vegetarian."

    goal = (form.get("goal") or "").strip()
    if goal not in GOAL_ADJUST:
        errors["goal"] = "Please select a goal."

    allergies_raw = (form.get("allergies") or "").strip()
    allergies = [a.strip().strip(",") for a in re_split(allergies_raw)]

    return errors, {
        "age": age, "sex": sex, "height_cm": height, "weight_kg": weight,
        "activity": activity, "diet_type": diet_type, "goal": goal,
        "allergies": [a for a in allergies if a],
        "analysis": None,
    }


def re_split(val):
    return [x for x in (v.strip() for v in val.split(",")) if x]