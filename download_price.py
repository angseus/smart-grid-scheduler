import xlrd
from xlrd.sheet import ctype_text

# Get a tuple of hourly pricing for the following day from an excel file
def downloadPrice(excel_file):

    values = {}

    # Open the workbook
    xl_workbook = xlrd.open_workbook(excel_file)

    # Get the relevant datasheet
    xl_sheet = xl_workbook.sheet_by_name(xl_workbook.sheet_names()[0])
    #xl_sheet = xl_workbook.sheet_by_index(0)
    
    for i in range(0,24):
        # 2 rows offset and always column 1
        cell_obj = xl_sheet.cell(i+2, 1)            
        
        # Add price to dict
        values.update({ i : (int (cell_obj.value) / 1000 ) })

        i += 1

    return values
    
if __name__ == "__main__":
    # This should not be used
    downloadPrice("elspot_prices.xls")
