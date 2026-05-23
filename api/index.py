from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

app.secret_key = "derivative-calculator-secret-key"


def parse_number_list(text):
    try:
        values = [float(item.strip()) for item in text.split(",") if item.strip()]
    except ValueError:
        raise ValueError("Please enter valid numbers separated by commas.")

    if len(values) < 2:
        raise ValueError("Please enter at least two values.")

    return values


def add_polynomials(poly1, poly2):
    max_length = max(len(poly1), len(poly2))
    result = [0.0] * max_length

    for i in range(max_length):
        a = poly1[i] if i < len(poly1) else 0.0
        b = poly2[i] if i < len(poly2) else 0.0
        result[i] = a + b

    return result


def multiply_polynomials(poly1, poly2):
    result = [0.0] * (len(poly1) + len(poly2) - 1)

    for i, a in enumerate(poly1):
        for j, b in enumerate(poly2):
            result[i + j] += a * b

    return result


def scale_polynomial(poly, scalar):
    return [coefficient * scalar for coefficient in poly]


def lagrange_interpolation_coefficients(x_values, y_values):
    polynomial = [0.0]

    for i in range(len(x_values)):
        basis = [1.0]

        for j in range(len(x_values)):
            if i != j:
                denominator = x_values[i] - x_values[j]

                if denominator == 0:
                    raise ValueError("X values must not contain duplicate values.")

                factor = [-x_values[j] / denominator, 1.0 / denominator]
                basis = multiply_polynomials(basis, factor)

        term = scale_polynomial(basis, y_values[i])
        polynomial = add_polynomials(polynomial, term)

    return polynomial


def derivative_coefficients(polynomial):
    if len(polynomial) <= 1:
        return [0.0]

    derivative = []

    for power in range(1, len(polynomial)):
        derivative.append(polynomial[power] * power)

    return derivative


def evaluate_polynomial(polynomial, x):
    total = 0.0

    for power, coefficient in enumerate(polynomial):
        total += coefficient * (x ** power)

    return total


def clean_number(value):
    if abs(value) < 1e-10:
        value = 0

    value = round(value, 6)

    if value == int(value):
        return str(int(value))

    return str(value).rstrip("0").rstrip(".")


def polynomial_to_latex(polynomial):
    terms = []

    for power in range(len(polynomial) - 1, -1, -1):
        coefficient = polynomial[power]

        if abs(coefficient) < 1e-10:
            continue

        coefficient_text = clean_number(abs(coefficient))

        if power == 0:
            term = coefficient_text
        elif power == 1:
            term = "x" if coefficient_text == "1" else f"{coefficient_text}x"
        else:
            term = f"x^{{{power}}}" if coefficient_text == "1" else f"{coefficient_text}x^{{{power}}}"

        if not terms:
            terms.append(f"-{term}" if coefficient < 0 else term)
        else:
            terms.append(f"- {term}" if coefficient < 0 else f"+ {term}")

    return " ".join(terms) if terms else "0"


@app.route("/", methods=["GET", "POST"])
def index():
    empty_form_data = {
        "x_values": "",
        "y_values": "",
        "evaluate_x": ""
    }

    if request.method == "POST":
        form_data = {
            "x_values": request.form.get("x_values", ""),
            "y_values": request.form.get("y_values", ""),
            "evaluate_x": request.form.get("evaluate_x", "")
        }

        try:
            x_values = parse_number_list(form_data["x_values"])
            y_values = parse_number_list(form_data["y_values"])
            evaluate_x = float(form_data["evaluate_x"])

            if len(x_values) != len(y_values):
                raise ValueError("X values and Y values must have the same length.")

            if len(set(x_values)) != len(x_values):
                raise ValueError("X values must not contain duplicate values.")

            polynomial = lagrange_interpolation_coefficients(x_values, y_values)
            derivative = derivative_coefficients(polynomial)
            derivative_value = evaluate_polynomial(derivative, evaluate_x)

            table_rows = [
                {
                    "x": clean_number(x),
                    "y": clean_number(y)
                }
                for x, y in zip(x_values, y_values)
            ]

            session["calculation_data"] = {
                "form_data": form_data,
                "result": clean_number(derivative_value),
                "error": None,
                "table_rows": table_rows,
                "polynomial_latex": polynomial_to_latex(polynomial),
                "derivative_latex": polynomial_to_latex(derivative)
            }

        except Exception as exception:
            session["calculation_data"] = {
                "form_data": form_data,
                "result": None,
                "error": str(exception),
                "table_rows": [],
                "polynomial_latex": None,
                "derivative_latex": None
            }

        return redirect(url_for("index", calculated="1"))

    calculation_data = None

    if request.args.get("calculated") == "1":
        calculation_data = session.pop("calculation_data", None)

    if calculation_data:
        return render_template(
            "index.html",
            form_data=calculation_data["form_data"],
            result=calculation_data["result"],
            error=calculation_data["error"],
            table_rows=calculation_data["table_rows"],
            polynomial_latex=calculation_data["polynomial_latex"],
            derivative_latex=calculation_data["derivative_latex"]
        )

    return render_template(
        "index.html",
        form_data=empty_form_data,
        result=None,
        error=None,
        table_rows=[],
        polynomial_latex=None,
        derivative_latex=None
    )


if __name__ == "__main__":
    app.run(debug=True)