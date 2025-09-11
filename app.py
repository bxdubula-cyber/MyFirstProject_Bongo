from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'supersecretkey'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            try:
                df = pd.read_excel(filepath)
                required_columns = {'date', 'income', 'expenses'}
                if not required_columns.issubset(df.columns):
                    flash('Error: The uploaded file must contain "date", "income", and "expenses" columns.')
                    return redirect(request.url)
                df['date'] = pd.to_datetime(df['date'])
                df['month_year'] = df['date'].dt.strftime('%B %Y')
                monthly_summary = df.groupby('month_year', sort=False).agg({
                    'income': 'sum',
                    'expenses': 'sum'
                }).reset_index()
                highest_income_row = monthly_summary.loc[monthly_summary['income'].idxmax()]
                highest_income = {
                    'month': highest_income_row['month_year'],
                    'value': f"${highest_income_row['income']:,.2f}"
                }
                lowest_income_row = monthly_summary.loc[monthly_summary['income'].idxmin()]
                lowest_income = {
                    'month': lowest_income_row['month_year'],
                    'value': f"${lowest_income_row['income']:,.2f}"
                }
                highest_expense_row = monthly_summary.loc[monthly_summary['expenses'].idxmax()]
                highest_expense = {
                    'month': highest_expense_row['month_year'],
                    'value': f"${highest_expense_row['expenses']:,.2f}"
                }
                lowest_expense_row = monthly_summary.loc[monthly_summary['expenses'].idxmin()]
                lowest_expense = {
                    'month': lowest_expense_row['month_year'],
                    'value': f"${lowest_expense_row['expenses']:,.2f}"
                }
                avg_income = f"${monthly_summary['income'].mean():,.2f}"
                avg_expense = f"${monthly_summary['expenses'].mean():,.2f}"
                summary_stats = {
                    'highest_income': highest_income,
                    'lowest_income': lowest_income,
                    'avg_income': avg_income,
                    'highest_expense': highest_expense,
                    'lowest_expense': lowest_expense,
                    'avg_expense': avg_expense
                }
                chart_data = {
                    'labels': monthly_summary['month_year'].tolist(),
                    'income_data': monthly_summary['income'].tolist(),
                    'expenses_data': monthly_summary['expenses'].tolist()
                }
                monthly_details = monthly_summary.set_index('month_year').to_dict('index')
                return render_template('results.html', 
                                       summary_stats=summary_stats, 
                                       chart_data=chart_data,
                                       monthly_details=monthly_details)
            except Exception as e:
                flash(f'An error occurred processing the file: {e}')
                return redirect(request.url)
        else:
            flash('Invalid file format. Please upload an .xlsx file.')
            return redirect(request.url)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)