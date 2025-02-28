from marshmallow import Schema, fields, validate

class OrderSchema(Schema):
    """
    Schema for serializing and validating order data.
    """
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    total_price = fields.Float(required=True, validate=validate.Range(min=0))
    status = fields.Str(validate=validate.OneOf(["pending", "completed", "cancelled"]))
    created_at = fields.DateTime()
    updated_at = fields.DateTime()

    class Meta:
        fields = ("id", "user_id", "total_price", "status", "created_at", "updated_at")
