def validate_price(price):
    if price is None:
        return False, "Price cannot be empty"
    try:
        val = float(price)
        if val < 0:
            return False, "Price must be non-negative"
        return True, ""
    except ValueError:
        return False, "Price must be a number"

def validate_stock(stock):
    if stock is None:
        return False, "Stock cannot be empty"
    try:
        val = int(stock)
        if val < 0:
            return False, "Stock must be non-negative"
        return True, ""
    except ValueError:
        return False, "Stock must be an integer"

def validate_design_no(design_no, existing_design_nos):
    if not design_no or not str(design_no).strip():
        return False, "Design Number is required"
    if str(design_no).strip() in [str(x) for x in existing_design_nos]:
        return False, "Design Number already exists"
    return True, ""
