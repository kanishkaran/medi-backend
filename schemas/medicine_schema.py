from marshmallow import Schema, fields, validate

class MedicineSchema(Schema):
    """
    Schema for serializing and validating medicine data.
    """
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1))
    description = fields.Str()
    price = fields.Float(required=True, validate=validate.Range(min=0))
    stock = fields.Int(required=True, validate=validate.Range(min=0))
    image_url = fields.Str()

    class Meta:
        fields = ("id", "name", "description", "price", "stock", "image_url")
