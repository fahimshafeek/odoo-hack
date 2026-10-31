# Catalog API Reference

Base URL: `http://localhost:8000`  
Authentication: `Authorization: Bearer <JWT>`

## Endpoints

| Method | Path | Allowed Roles | Description |
|---|---|---|---|
| `GET` | `/products` | admin, staff | List products (params: `page`, `page_size`, `q`, `type`, `active`) |
| `POST` | `/products` | admin | Create product with sales & cost price |
| `GET` | `/products/{id}` | admin, staff | Get product detail with attributes and variant values |
| `PATCH` | `/products/{id}` | admin | Update product details |
| `DELETE` | `/products/{id}` | admin | Deactivate if referenced, else hard delete |
| `POST` | `/products/{id}/attributes` | admin | Add attribute with values and extra prices |
| `PATCH` | `/products/{id}/attributes/{attr_id}` | admin | Diff-update attribute values |
| `DELETE` | `/products/{id}/attributes/{attr_id}` | admin | Delete product attribute |
| `GET` | `/plans` | admin, staff | List subscription plans |
| `POST` | `/plans` | admin | Create plan with rule flags |
| `GET` | `/plans/{id}` | admin, staff | Get plan details |
| `PATCH` | `/plans/{id}` | admin | Update plan rules |
| `POST` | `/plans/{id}/close` | admin | Close plan (sets `is_active=false`) |
| `DELETE` | `/plans/{id}` | admin | Deactivate if referenced, else delete |
| `GET` | `/payment-terms` | admin, staff | List payment terms |
| `POST` | `/payment-terms` | admin | Create payment term (`due_days` 0..365) |
| `GET` | `/payment-terms/{id}` | admin, staff | Get payment term |
| `PATCH` | `/payment-terms/{id}` | admin | Update payment term |
| `DELETE` | `/payment-terms/{id}` | admin | Delete payment term |
| `GET` | `/quotation-templates` | admin, staff | List quotation templates |
| `POST` | `/quotation-templates` | admin | Create quotation template with line bundle |
| `GET` | `/quotation-templates/{id}` | admin, staff | Get quotation template detail |
| `PATCH` | `/quotation-templates/{id}` | admin | Update quotation template |
| `DELETE` | `/quotation-templates/{id}` | admin | Delete quotation template |

## Sample Requests & Responses

### 1. Create Product with Soft Warning
`POST /products`
```json
{
  "name": "Cloud Server Pro",
  "type": "infrastructure",
  "sales_price": "1000.00",
  "cost_price": "1200.00",
  "is_active": true
}
```
Response `201 Created`:
```json
{
  "id": "e5b8d6fc-31ab-435e-9907-7389a1c1d0b2",
  "name": "Cloud Server Pro",
  "type": "infrastructure",
  "sales_price": "1000.00",
  "cost_price": "1200.00",
  "is_active": true,
  "warnings": ["cost_price_exceeds_sales_price"],
  "attributes": []
}
```

### 2. Add Attribute and Variant Extra Price
`POST /products/e5b8d6fc-31ab-435e-9907-7389a1c1d0b2/attributes`
```json
{
  "name": "Brand",
  "values": [
    { "name": "Odoo", "extra_price": "560.00" },
    { "name": "Community", "extra_price": "0.00" }
  ]
}
```
Response `201 Created`:
```json
{
  "id": "e5b8d6fc-31ab-435e-9907-7389a1c1d0b2",
  "name": "Cloud Server Pro",
  "attributes": [
    {
      "id": "89b7cf3a-...",
      "name": "Brand",
      "values": [
        { "id": "12b8cd9f-...", "name": "Odoo", "extra_price": "560.00" },
        { "id": "45f910ab-...", "name": "Community", "extra_price": "0.00" }
      ]
    }
  ]
}
```
