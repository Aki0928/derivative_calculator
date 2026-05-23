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

    return [polynomial[power] * power for power in range(1, len(polynomial))]


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


def format_lagrange_factor(x_value):
    if x_value == 0:
        return "x"

    if x_value < 0:
        return f"(x + {clean_number(abs(x_value))})"

    return f"(x - {clean_number(x_value)})"


def build_lagrange_basis_text(x_values, i):
    numerator_parts = []
    denominator_parts = []

    for j in range(len(x_values)):
        if i != j:
            numerator_parts.append(format_lagrange_factor(x_values[j]))
            denominator_parts.append(
                f"({clean_number(x_values[i])} - {clean_number(x_values[j])})"
            )

    numerator = "".join(numerator_parts)
    denominator = "".join(denominator_parts)

    return numerator, denominator


def build_solution_steps(x_values, y_values, evaluate_x, polynomial, derivative, derivative_value):
    point_text = ",\\ ".join([
        f"({clean_number(x)}, {clean_number(y)})"
        for x, y in zip(x_values, y_values)
    ])

    basis_html = ""

    for i in range(len(x_values)):
        numerator, denominator = build_lagrange_basis_text(x_values, i)

        basis_html += f"""
            <div class="formula-box">
                \\[
                L_{{{i}}}(x)=
                \\frac{{{numerator}}}{{{denominator}}}
                \\]
            </div>
        """

    polynomial_expression = " + ".join([
        f"{clean_number(y_values[i])}L_{{{i}}}(x)"
        for i in range(len(y_values))
    ])

    polynomial_latex = polynomial_to_latex(polynomial)
    derivative_latex = polynomial_to_latex(derivative)

    return [
        {
            "title": "Write the given data points",
            "body": f"""
                <p>The given points are:</p>
                <div class="formula-box">
                    \\[
                    {point_text}
                    \\]
                </div>
            """
        },
        {
            "title": "Use the Lagrange interpolation formula",
            "body": """
                <p>The Lagrange interpolation formula is:</p>
                <div class="formula-box">
                    \\[
                    P(x)=\\sum_{i=0}^{n} y_iL_i(x)
                    \\]
                </div>

                <p>where:</p>
                <div class="formula-box">
                    \\[
                    L_i(x)=
                    \\prod_{j=0, j \\neq i}^{n}
                    \\frac{x-x_j}{x_i-x_j}
                    \\]
                </div>
            """
        },
        {
            "title": "Find the basis polynomials",
            "body": basis_html
        },
        {
            "title": "Substitute the y-values",
            "body": f"""
                <p>Using the given y-values:</p>
                <div class="formula-box">
                    \\[
                    P(x)={polynomial_expression}
                    \\]
                </div>
            """
        },
        {
            "title": "Simplify the interpolating polynomial",
            "body": f"""
                <p>After simplifying the polynomial:</p>
                <div class="formula-box">
                    \\[
                    P(x)={polynomial_latex}
                    \\]
                </div>
            """
        },
        {
            "title": "Differentiate the polynomial",
            "body": f"""
                <p>Differentiate \\(P(x)\\):</p>
                <div class="formula-box">
                    \\[
                    P'(x)={derivative_latex}
                    \\]
                </div>
            """
        },
        {
            "title": "Evaluate the derivative",
            "body": f"""
                <p>Substitute \\(x={clean_number(evaluate_x)}\\):</p>
                <div class="formula-box">
                    \\[
                    P'({clean_number(evaluate_x)})={clean_number(derivative_value)}
                    \\]
                </div>

                <div class="answer-box">
                    Final Answer: \\(P'({clean_number(evaluate_x)})={clean_number(derivative_value)}\\)
                </div>
            """
        }
    ]


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

            solution_steps = build_solution_steps(
                x_values,
                y_values,
                evaluate_x,
                polynomial,
                derivative,
                derivative_value
            )

            session["calculation_data"] = {
                "form_data": form_data,
                "result": clean_number(derivative_value),
                "error": None,
                "table_rows": table_rows,
                "polynomial_latex": polynomial_to_latex(polynomial),
                "derivative_latex": polynomial_to_latex(derivative),
                "solution_steps": solution_steps
            }

        except Exception as exception:
            session["calculation_data"] = {
                "form_data": form_data,
                "result": None,
                "error": str(exception),
                "table_rows": [],
                "polynomial_latex": None,
                "derivative_latex": None,
                "solution_steps": []
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
            derivative_latex=calculation_data["derivative_latex"],
            solution_steps=calculation_data["solution_steps"]
        )

    return render_template(
        "index.html",
        form_data=empty_form_data,
        result=None,
        error=None,
        table_rows=[],
        polynomial_latex=None,
        derivative_latex=None,
        solution_steps=[]
    )


if __name__ == "__main__":
    app.run(debug=True)
