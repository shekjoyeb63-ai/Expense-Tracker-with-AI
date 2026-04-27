from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.tables import sesssionLocal
from app.models.operations import Expense_tracker
from datetime import datetime
from app.services.redis_client import redis_client
from app.services.ai_client import categorize_expense, get_expense_insights, scan_receipt
import base64
import json

expenses_bp = Blueprint("expenses", __name__)
tracker = Expense_tracker()


def get_db():
    if "db" not in g:
        g.db = sesssionLocal()
    return g.db


def input_validation(title, amount, category, date):
    errors = []
    if not title or not isinstance(title, str) or not title.strip():
        errors.append("Title must not be blank and must be valid text")
    if amount is None:
        errors.append("Amount is required")
    elif not isinstance(amount, (int, float)):
        errors.append("Amount must be a valid number")
    elif amount < 0:
        errors.append("Amount cannot be negative")
    if not category or not isinstance(category, str) or not category.strip():
        errors.append("Please select a valid category")
    if not date:
        errors.append("Date is required")
    else:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            errors.append("Date must be in YYYY-MM-DD format")
    return errors



@expenses_bp.route("/view", methods=["GET"])
@jwt_required()
def view_expense():
    """
    View all expenses (paginated)
    ---
    tags:
      - Expenses
    security:
      - BearerAuth: []
    responses:
      200:
        description: List of expenses
    """
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 10, type=int)
    cache_key=f"expenses : {user_id}:page:{page}:page_size:{page_size}"
    cached=redis_client.get(cache_key)
    if cached:
        return jsonify(json.loads(cached)),200
    data, status = tracker.view_expense(page, page_size, user_id)
    if status==200:
        redis_client.setex(cache_key,60,json.dumps(data))
    return jsonify(data), status



@expenses_bp.route("/add", methods=["POST"])
@jwt_required()
def add():
    """
    Add a new expense
    ---
    tags:
      - Expenses
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: Groceries
            amount:
              type: number
              example: 500
            category:
              type: string
              example: Food
            date:
              type: string
              example: "2026-04-25"
    responses:
      201:
        description: Expense added successfully
      422:
        description: Validation error
    """
    if not request.json:
        return jsonify({"message": "Request body must be JSON"}), 400

    user_id = get_jwt_identity()
    title = request.json.get("title")
    amount = request.json.get("amount")
    category = request.json.get("category")
    date = request.json.get("date")
    if not category or category.strip() == "":
        category = categorize_expense(title)

    errors = input_validation(title, amount, category, date)
    if errors:
        return jsonify({"errors": errors}), 422
    data, status = tracker.add_expense(title, amount, category, date, user_id)
    if status==201:
        redis_client.delete(f"total:{user_id}")
        for key in redis_client.scan_iter(f"expenses:{user_id}*"):
            redis_client.delete(key)
    return jsonify(data), status



@expenses_bp.route("/delete", methods=["DELETE"])
@jwt_required()
def delete():
    """
    Delete an expense by title
    ---
    tags:
      - Expenses
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: Groceries
    responses:
      200:
        description: Deleted successfully
      404:
        description: Not found
    """
    if not request.json:
        return jsonify({"message": "Request body must be JSON"}), 400

    user_id = get_jwt_identity()
    title = request.json.get("title")
    data, status = tracker.delete_titl(title, user_id)
    if status==201:
        redis_client.delete(f"total:{user_id}")
        for key in redis_client.scan_iter(f"expenses:{user_id}*"):
            redis_client.delete(key)
    return jsonify(data), status



@expenses_bp.route("/search", methods=["POST"])
@jwt_required()
def search():
    """
    Search expenses by category
    ---
    tags:
      - Expenses
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            category:
              type: string
              example: Food
    responses:
      200:
        description: Matching expenses
      404:
        description: Category not found
    """
    if not request.json:
        return jsonify({"message": "Request body must be JSON"}), 400

    user_id = get_jwt_identity()
    category = request.json.get("category")
    data, status = tracker.search_by_cat(category, user_id)
    return jsonify(data), status



@expenses_bp.route("/view_total", methods=["GET"])
@jwt_required()
def view_total():
    """
    View total expense amount
    ---
    tags:
      - Expenses
    security:
      - BearerAuth: []
    responses:
      200:
        description: Total amount
    """
    user_id = get_jwt_identity()
    cache_key=f"total:{user_id}"
    cached=redis_client.get(cache_key)
    if cached:
        return jsonify(json.loads(cached)),200
    data, status = tracker.view_total(user_id)
    if status==200:
        redis_client.setex(cache_key,60,json.dumps(data))
    return jsonify(data), status



@expenses_bp.route("/date_range", methods=["POST"])
@jwt_required()
def search_by_date():
    """
    Filter expenses by date range
    ---
    tags:
      - Expenses
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            start_date:
              type: string
              example: "2026-04-01"
            end_date:
              type: string
              example: "2026-04-30"
    responses:
      200:
        description: Filtered expenses
    """
    if not request.json:
        return jsonify({"message": "Request body must be JSON"}), 400

    user_id = get_jwt_identity()
    start_date = request.json.get("start_date")
    end_date = request.json.get("end_date")
    data, status = tracker.filter_Expenses_bydate(start_date, end_date, user_id)
    return jsonify({"message": data}), status

@expenses_bp.route("/chat", methods=["POST"])
@jwt_required()
def chat():
    """
    AI-powered expense insights chatbot
    ---
    tags:
      - AI
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            message:
              type: string
              example: "How much did I spend on food this month?"
    responses:
      200:
        description: AI response
    """
    if not request.json:
        return jsonify({"message": "Request body must be JSON"}), 400

    user_id = get_jwt_identity()
    user_message = request.json.get("message")

    if not user_message:
        return jsonify({"message": "Message is required"}), 400

    db = get_db()
    from app.models.tables import Expenses
    expenses = db.query(Expenses).filter(
        Expenses.user_id == user_id
    ).all()

    expense_data = {
        "expenses": [e.to_dict() for e in expenses],
        "total_count": len(expenses),
        "total_amount": sum(e.amount for e in expenses)
    }
    answer = get_expense_insights(user_message, expense_data)

    return jsonify({"answer": answer}), 200


@expenses_bp.route("/scan-receipt", methods=["POST"])
@jwt_required()
def scan_receipt_route():
    """
    Scan receipt image and auto-create expense
    ---
    tags:
      - AI
    security:
      - BearerAuth: []
    responses:
      201:
        description: Expense created from receipt
    """
    user_id = get_jwt_identity()

    if "receipt" not in request.files:
        return jsonify({"message": "No receipt image uploaded"}), 400

    file = request.files["receipt"]
    image_data = base64.b64encode(file.read()).decode("utf-8")
    extracted = scan_receipt(image_data)

    if not extracted.get("amount"):
        return jsonify({"message": "Could not extract amount from receipt"}), 422

    data, status = tracker.add_expense(
        title=extracted.get("merchant") or "Receipt",
        amount=extracted["amount"],
        category=extracted.get("category") or "Other",
        date=extracted.get("date") or datetime.now().strftime("%Y-%m-%d"),
        user_id=user_id
    )

    return jsonify({
        "message": "Expense created from receipt",
        "extracted": extracted,
        "expense": data
    }), status