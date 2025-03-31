from database import db
from models import Medicine

def get_medicine_details(medicine_name):
    """
    Fetches basic details of a medicine based on its name.
    :param medicine_name: Name of the medicine
    :return: A dictionary containing medicine details or None if not found
    """
    try:
        # Query the Medicine table using SQLAlchemy ORM
        query = db.session.query(
            Medicine.id,
            Medicine.name,
            Medicine.pack_size_label,
            Medicine.price,
            Medicine.image_url
        ).filter(Medicine.name.ilike(f"%{medicine_name}%"))

        result = query.first()  # Fetch the first result as a tuple

        # Handle the result as a tuple
        if result:
            return {
                "id": result[0],
                "name": result[1],
                "pack_size_label": result[2],
                "price": result[3],
                "image_url": result[4]
            }
        return result

    except Exception as e:
        return f"Error: {str(e)}"


def get_medicine_availability(medicine_name):
    """
    Fetches the stocks remaining of a medicine based on its name.
    :param medicine_name: Name of the medicine
    :return: A dictionary containing medicine details or None if not found
    """
    try:
        # Query the Medicine table using SQLAlchemy ORM
        query = db.session.query(
            Medicine.id,
            Medicine.name,
            Medicine.stock
        ).filter(Medicine.name.ilike(f"%{medicine_name}%"))

        result = query.first()  # Fetch the first result as a tuple

        # Handle the result as a tuple
        if result:
            return {
                "id": result[0],
                "name": result[1],
                "stock": result[2]
            }
        return None

    except Exception as e:
        return f"Error: {str(e)}"


def get_medicine_info(medicine_name):
    """
    Fetches detailed information about a medicine.
    :param medicine_name: Name of the medicine
    :return: A dictionary containing detailed medicine information or None if not found
    """
    try:
        # Query the Medicine table using SQLAlchemy ORM
        query = db.session.query(
            Medicine.name,
            Medicine.uses,
            Medicine.side_effects,
            Medicine.manufacturer
        ).filter(Medicine.name.ilike(f"%{medicine_name}%"))

        result = query.first()  # Fetch the first result as a tuple

        # Handle the result as a tuple
        if result:
            return {
                "name": result[0],
                "uses": result[1],
                "side_effects": result[2],
                "manufacturer": result[3]
            }
        return None

    except Exception as e:
        return f"Error: {str(e)}"

