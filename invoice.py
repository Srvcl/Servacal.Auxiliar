import pandas as pd
import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

class InvoiceGenerator:
    def __init__(self, clients_csv_path, works_csv_path, tax_rate=0.21):
        """
        Initialize the Invoice Generator
        
        Args:
            clients_csv_path (str): Path to CSV file containing client data
            works_csv_path (str): Path to CSV file containing work/service data
            tax_rate (float): Tax rate (default 21% = 0.21)
        """
        self.clients_csv_path = clients_csv_path
        self.works_csv_path = works_csv_path
        self.tax_rate = tax_rate
        
        # Load data
        self.clients_df = self.load_clients_data()
        self.works_df = self.load_works_data()
    
    def load_clients_data(self):
        """Load client data from CSV file"""
        try:
            df = pd.read_csv(self.clients_csv_path)
            # Clean column names (remove whitespace)
            df.columns = df.columns.str.strip()
            print(f"Loaded {len(df)} clients from {self.clients_csv_path}")
            return df
        except FileNotFoundError:
            print(f"Error: Client file '{self.clients_csv_path}' not found")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error loading client data: {e}")
            return pd.DataFrame()
    
    def load_works_data(self):
        """Load works/services data from CSV file"""
        try:
            df = pd.read_csv(self.works_csv_path)
            # Clean column names (remove whitespace)
            df.columns = df.columns.str.strip()
            # Convert date column to datetime if it exists
            if 'date' in df.columns.str.lower():
                date_col = [col for col in df.columns if 'date' in col.lower()][0]
                df[date_col] = pd.to_datetime(df[date_col])
            print(f"Loaded {len(df)} work records from {self.works_csv_path}")
            return df
        except FileNotFoundError:
            print(f"Error: Works file '{self.works_csv_path}' not found")
            return pd.DataFrame()
        except Exception as e:
            print(f"Error loading works data: {e}")
            return pd.DataFrame()
    
    def get_client_data(self, client_id):
        """
        Retrieve client data by ID
        
        Args:
            client_id: The client ID to search for
            
        Returns:
            dict: Client data or None if not found
        """
        # Try different possible column names for client ID
        id_columns = ['id', 'client_id', 'ID', 'Client_ID', 'id_number', 'ID_Number']
        client_id_col = None
        
        for col in id_columns:
            if col in self.clients_df.columns:
                client_id_col = col
                break
        
        if client_id_col is None:
            print("Error: Could not find client ID column in clients data")
            return None
        
        # Debug: Print available client IDs and their types
        print(f"Debug: Looking for client ID '{client_id}' (type: {type(client_id)})")
        print(f"Debug: Available client IDs: {self.clients_df[client_id_col].tolist()}")
        print(f"Debug: Client ID types: {[type(x) for x in self.clients_df[client_id_col].tolist()]}")
        
        # Convert both to string for comparison to handle type mismatches
        client_id_str = str(client_id)
        client_row = self.clients_df[self.clients_df[client_id_col].astype(str) == client_id_str]
        
        if client_row.empty:
            print(f"Error: Client with ID '{client_id}' not found")
            return None
        
        return client_row.iloc[0].to_dict()
    
    def get_client_works(self, client_id):
        """
        Retrieve all works for a specific client
        
        Args:
            client_id: The client ID to search for
            
        Returns:
            DataFrame: Works data for the client
        """
        # Try different possible column names for client ID in works data
        id_columns = ['client_id', 'Client_ID', 'id', 'ID', 'client', 'Client']
        client_id_col = None
        
        for col in id_columns:
            if col in self.works_df.columns:
                client_id_col = col
                break
        
        if client_id_col is None:
            print("Error: Could not find client ID column in works data")
            return pd.DataFrame()
        
        client_works = self.works_df[self.works_df[client_id_col] == client_id].copy()
        return client_works
    
    def calculate_invoice_totals(self, works_df):
        """
        Calculate invoice totals from works data
        
        Args:
            works_df (DataFrame): Works data for a client
            
        Returns:
            dict: Dictionary containing subtotal, tax, and total amounts
        """
        # Try different possible column names for amounts
        amount_columns = ['amount', 'import', 'price', 'cost', 'value', 'total', 'Amount', 'Import', 'Price']
        amount_col = None
        
        for col in amount_columns:
            if col in works_df.columns:
                amount_col = col
                break
        
        if amount_col is None:
            print("Error: Could not find amount column in works data")
            return {'subtotal': 0, 'tax': 0, 'total': 0}
        
        # Calculate subtotal
        subtotal = works_df[amount_col].sum()
        
        # Calculate tax
        tax_amount = subtotal * self.tax_rate
        
        # Calculate total
        total = subtotal + tax_amount
        
        return {
            'subtotal': round(subtotal, 2),
            'tax': round(tax_amount, 2),
            'total': round(total, 2)
        }
    
    def generate_invoice(self, client_id, invoice_number=None, invoice_date=None):
        """
        Generate a complete invoice for a client
        
        Args:
            client_id: The client ID
            invoice_number (str): Invoice number (auto-generated if None)
            invoice_date (str): Invoice date (today if None)
            
        Returns:
            dict: Complete invoice data
        """
        # Get client data
        client_data = self.get_client_data(client_id)
        if client_data is None:
            return None
        
        # Get client works
        client_works = self.get_client_works(client_id)
        if client_works.empty:
            print(f"Warning: No works found for client ID '{client_id}'")
        
        # Calculate totals
        totals = self.calculate_invoice_totals(client_works)
        
        # Generate invoice number if not provided
        if invoice_number is None:
            invoice_number = f"INV-{datetime.datetime.now().strftime('%Y%m%d')}-{client_id}"
        
        # Set invoice date if not provided
        if invoice_date is None:
            invoice_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # Create invoice dictionary
        invoice = {
            'invoice_number': invoice_number,
            'invoice_date': invoice_date,
            'client_data': client_data,
            'works': client_works.to_dict('records'),
            'subtotal': totals['subtotal'],
            'tax_rate': self.tax_rate * 100,  # Convert to percentage
            'tax_amount': totals['tax'],
            'total_amount': totals['total']
        }
        
        return invoice
    
    def print_invoice(self, invoice):
        """Print invoice in a formatted way"""
        if invoice is None:
            print("No invoice to print")
            return
        
        print("=" * 60)
        print(f"INVOICE #{invoice['invoice_number']}")
        print("=" * 60)
        print(f"Date: {invoice['invoice_date']}")
        print()
        
        # Client information
        print("BILL TO:")
        client = invoice['client_data']
        
        # Try to get client name from different possible columns
        name_columns = ['name', 'company_name', 'client_name', 'Name', 'Company_Name', 'Client_Name']
        client_name = "Unknown Client"
        for col in name_columns:
            if col in client and pd.notna(client[col]):
                client_name = client[col]
                break
        
        print(f"  {client_name}")
        
        # Print address if available
        address_columns = ['address', 'Address', 'street', 'Street']
        for col in address_columns:
            if col in client and pd.notna(client[col]):
                print(f"  {client[col]}")
                break
        
        # Print zip code if available
        zip_columns = ['zip_code', 'zip', 'postal_code', 'Zip_Code', 'ZIP', 'Postal_Code']
        for col in zip_columns:
            if col in client and pd.notna(client[col]):
                print(f"  {client[col]}")
                break
        
        print()
        
        # Works/Services
        print("SERVICES:")
        print("-" * 60)
        print(f"{'Description':<30} {'Date':<12} {'Amount':<10}")
        print("-" * 60)
        
        for work in invoice['works']:
            # Get description
            desc_columns = ['description', 'concept', 'service', 'Description', 'Concept', 'Service']
            description = "Service"
            for col in desc_columns:
                if col in work and pd.notna(work[col]):
                    description = str(work[col])[:28]  # Truncate if too long
                    break
            
            # Get date
            date_columns = ['date', 'Date', 'work_date', 'Work_Date']
            work_date = "N/A"
            for col in date_columns:
                if col in work and pd.notna(work[col]):
                    if isinstance(work[col], str):
                        work_date = work[col][:10]  # Take first 10 chars for date
                    else:
                        work_date = str(work[col])[:10]
                    break
            
            # Get amount
            amount_columns = ['amount', 'import', 'price', 'cost', 'value', 'total', 'Amount', 'Import', 'Price']
            amount = 0
            for col in amount_columns:
                if col in work and pd.notna(work[col]):
                    amount = work[col]
                    break
            
            print(f"{description:<30} {work_date:<12} ${amount:<9.2f}")
        
        print("-" * 60)
        print(f"{'Subtotal:':<54} ${invoice['subtotal']:>8.2f}")
        print(f"{'Tax (' + str(invoice['tax_rate']) + '%):':<54} ${invoice['tax_amount']:>8.2f}")
        print("=" * 60)
        print(f"{'TOTAL:':<54} ${invoice['total_amount']:>8.2f}")
        print("=" * 60)
    
    def save_invoice_to_file(self, invoice, filename=None):
        """Save invoice to a text file"""
        if invoice is None:
            print("No invoice to save")
            return
        
        if filename is None:
            filename = f"invoice_{invoice['invoice_number']}.txt"
        
        # Redirect print output to file
        import sys
        original_stdout = sys.stdout
        
        try:
            with open(filename, 'w') as f:
                sys.stdout = f
                self.print_invoice(invoice)
            sys.stdout = original_stdout
            print(f"Invoice saved to {filename}")
        except Exception as e:
            sys.stdout = original_stdout
            print(f"Error saving invoice: {e}")
    
    def save_invoice_to_pdf(self, invoice, filename=None):
        """Save invoice to a PDF file"""
        if invoice is None:
            print("No invoice to save")
            return
        
        if filename is None:
            filename = f"invoice_{invoice['invoice_number']}.pdf"
        
        try:
            # Create PDF document
            doc = SimpleDocTemplate(filename, pagesize=A4, 
                                  rightMargin=72, leftMargin=72, 
                                  topMargin=72, bottomMargin=72)
            
            # Get styles
            styles = getSampleStyleSheet()
            
            # Create custom styles
            title_style = ParagraphStyle(
                'InvoiceTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.darkblue,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            header_style = ParagraphStyle(
                'InvoiceHeader',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=12,
                spaceBefore=20,
                textColor=colors.darkblue,
                fontName='Helvetica-Bold'
            )
            
            normal_style = ParagraphStyle(
                'InvoiceNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                leading=14,
                fontName='Helvetica'
            )
            
            client_style = ParagraphStyle(
                'ClientInfo',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=6,
                leading=16,
                fontName='Helvetica-Bold'
            )
            
            # Build PDF content
            story = []
            
            # Invoice title
            story.append(Paragraph("INVOICE", title_style))
            story.append(Spacer(1, 20))
            
            # Invoice number and date
            story.append(Paragraph(f"<b>Invoice #:</b> {str(invoice['invoice_number'])}", normal_style))
            story.append(Paragraph(f"<b>Date:</b> {str(invoice['invoice_date'])}", normal_style))
            story.append(Spacer(1, 20))
            
            # Client information
            story.append(Paragraph("BILL TO:", header_style))
            client = invoice['client_data']
            
            # Get client name
            name_columns = ['name', 'company_name', 'client_name', 'Name', 'Company_Name', 'Client_Name']
            client_name = "Unknown Client"
            for col in name_columns:
                if col in client and pd.notna(client[col]):
                    client_name = client[col]
                    break
            
            story.append(Paragraph(str(client_name), client_style))
            
            # Get address
            address_columns = ['address', 'Address', 'street', 'Street']
            for col in address_columns:
                if col in client and pd.notna(client[col]):
                    story.append(Paragraph(str(client[col]), normal_style))
                    break
            
            # Get zip code
            zip_columns = ['zip_code', 'zip', 'postal_code', 'Zip_Code', 'ZIP', 'Postal_Code']
            for col in zip_columns:
                if col in client and pd.notna(client[col]):
                    story.append(Paragraph(str(client[col]), normal_style))
                    break
            
            story.append(Spacer(1, 30))
            
            # Services table
            story.append(Paragraph("SERVICES:", header_style))
            story.append(Spacer(1, 10))
            
            # Prepare table data
            table_data = [['Description', 'Date', 'Amount']]
            
            for work in invoice['works']:
                # Get description
                desc_columns = ['description', 'concept', 'service', 'Description', 'Concept', 'Service']
                description = "Service"
                for col in desc_columns:
                    if col in work and pd.notna(work[col]):
                        description = str(work[col])
                        break
                
                # Get date
                date_columns = ['date', 'Date', 'work_date', 'Work_Date']
                work_date = "N/A"
                for col in date_columns:
                    if col in work and pd.notna(work[col]):
                        work_date = str(work[col])[:10]
                        break
                
                # Get amount
                amount_columns = ['amount', 'import', 'price', 'cost', 'value', 'total', 'Amount', 'Import', 'Price']
                amount = 0
                for col in amount_columns:
                    if col in work and pd.notna(work[col]):
                        amount = work[col]
                        break
                
                table_data.append([description, work_date, f"${amount:.2f}"])
            
            # Add totals row
            table_data.append(['', '', ''])
            table_data.append(['Subtotal:', '', f"${invoice['subtotal']:.2f}"])
            table_data.append([f'Tax ({invoice["tax_rate"]:.1f}%):', '', f"${invoice['tax_amount']:.2f}"])
            table_data.append(['TOTAL:', '', f"${invoice['total_amount']:.2f}"])
            
            # Create table
            table = Table(table_data, colWidths=[3.5*inch, 1.5*inch, 1*inch])
            table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),  # Amount column right-aligned
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                
                # Data rows
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -4), 1, colors.black),  # Grid for data rows
                ('LINEBELOW', (0, -4), (-1, -4), 2, colors.black),  # Line above totals
                
                # Totals rows
                ('FONTNAME', (0, -3), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, -3), (-1, -1), 11),
                ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),  # Line above final total
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),  # Highlight total row
            ]))
            
            story.append(table)
            story.append(Spacer(1, 30))
            
            # Footer
            story.append(Paragraph("Thank you for your business!", normal_style))
            story.append(Paragraph("For questions about this invoice, please contact us.", normal_style))
            
            # Build PDF
            doc.build(story)
            print(f"Invoice PDF saved to {filename}")
            
        except Exception as e:
            print(f"Error saving invoice to PDF: {e}")


# Example usage and demo
def main():
    """
    Example usage of the InvoiceGenerator
    
    Expected CSV file structures:
    
    clients.csv:
    - id, name (or company_name), address, zip_code, etc.
    
    works.csv:
    - client_id, date, description (or concept), amount (or import), etc.
    """
    
    # Initialize the invoice generator
    # You'll need to replace these paths with your actual CSV file paths
    generator = InvoiceGenerator(
        clients_csv_path="clients.csv",
        works_csv_path="works.csv",
        tax_rate=0.21  # 21% tax rate (adjust as needed)
    )
    
    # Example: Generate invoice for client with ID 12345
    client_id = 12345  # Replace with actual client ID
    
    # Generate the invoice
    invoice = generator.generate_invoice(client_id)
    
    if invoice:
        # Print the invoice to console
        generator.print_invoice(invoice)
        
        # Save invoice to text file
        generator.save_invoice_to_file(invoice)
        
        # Save invoice to PDF file
        generator.save_invoice_to_pdf(invoice)
    else:
        print("Failed to generate invoice")

if __name__ == "__main__":
    # Create sample CSV files for demonstration
    
    # Sample clients data
    clients_sample = pd.DataFrame({
        'id': ['12345', '67890', '11111'],
        'name': ['ABC Corporation', 'John Doe', 'XYZ Ltd'],
        'address': ['123 Main St', '456 Oak Ave', '789 Pine Rd'],
        'zip_code': ['10001', '90210', '12345']
    })
    clients_sample.to_csv('clients.csv', index=False)
    
    # Sample works data
    works_sample = pd.DataFrame({
        'client_id': [12345, 12345, 67890, 12345],  # Use integers to match client IDs
        'date': ['2024-01-15', '2024-01-20', '2024-01-18', '2024-01-25'],
        'description': ['Web Development', 'Database Setup', 'Consulting', 'Bug Fixes'],
        'amount': [1500.00, 800.00, 300.00, 400.00]
    })
    works_sample.to_csv('works.csv', index=False)
    
    print("Sample CSV files created: clients.csv and works.csv")
    print("\nRunning invoice generation demo...\n")
    
    # Run the main demo
    main()
