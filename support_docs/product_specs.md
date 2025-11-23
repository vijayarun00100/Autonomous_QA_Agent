# Product Specifications

## Discount Codes
- `SAVE15` applies a 15% discount to the pre-shipping subtotal.
- `FREESHIP` removes the shipping charge when any shipping method is selected.
- Only one discount code can be active per order.

## Shipping
- Standard shipping is free and delivers within 5-7 business days.
- Express shipping costs $10 and delivers within 2-3 business days.
- Express shipping cost is non-refundable unless `FREESHIP` is applied.

## Cart Rules
- Items must have a minimum quantity of 1.
- The cart cannot be submitted if empty.
- The grand total is calculated as `subtotal + shipping - discount`.

## Payment Success Criteria
- Payment success message appears only after all required fields are valid and at least one cart item exists.
- Supported payment methods: Credit Card and PayPal.
