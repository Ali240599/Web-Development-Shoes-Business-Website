from django.shortcuts import render
from django.views import View
from django.db import connection
import pandas as pd
import prophet

# Create your views here.

class Revenue_Products(View):
    def get(self, request, *args, **kwargs):
        cursor = connection.cursor()
        users = cursor.execute("SELECT sum(a.quantity) as total_quantity, b.name, b.price FROM customer_orderitem a, customer_item b where a.product_id = b.id group by a.product_id")
        data = cursor.fetchall()
        df = pd.DataFrame(data)
        print("Does not show column names")
        print(df)

        column_names = [desc[0] for desc in cursor.description]
        print(column_names)
        df.columns = column_names
        print("shows column names")
        print(df)
        df['sales_by_product'] = df.total_quantity * df.price
        df = df.sort_values('sales_by_product', ascending=False).iloc[:5]
        print(df)
        products = df['name'].tolist()
        sales_by_product = df['sales_by_product'].tolist()
        return render(request, 'store/revenue_by_products.html', {'products':products, 'sales_by_product':sales_by_product})

class Revenue_Categories(View):
    def get(self, request, *args, **kwargs):
        cursor = connection.cursor()
        users = cursor.execute("select cat_name, sum(price*total_quantity) as total_by_category from (SELECT a.product_id, b.name, b.price as price, c.name as cat_name, sum(a.quantity) as total_quantity  FROM customer_orderitem a, customer_item b, customer_category c, customer_item_category d where a.product_id = b.id and b.id = d.item_id and c.id = d.category_id group by a.product_id, b.name, b.price, c.name) as s group by cat_name;")
        data = cursor.fetchall()
        df = pd.DataFrame(data)
        print("Does not show column names")
        print(df)

        column_names = [desc[0] for desc in cursor.description]
        print(column_names)
        df.columns = column_names
        print("shows column names")
        print(df)
        
        df = df.sort_values('total_by_category', ascending=False).iloc[:5]
        print(df)
        categories = df['cat_name'].tolist()
        sales_by_category = df['total_by_category'].tolist()
        return render(request, 'store/revenue_by_categories.html', {'categories':categories, 'sales_by_category':sales_by_category})
    
import matplotlib.pyplot as plt
import io
import urllib, base64
from prophet import Prophet
from django.http import HttpResponse

class Revenue_Forecast(View):
    def get(self, request, *args, **kwargs):
        # Read data
        pizza_df = pd.read_excel('Shoes Sales.xlsx')   
        print(pizza_df.head(5))     

        # Prepare data for Prophet
        df = pizza_df.rename(columns={'Invoice Date': 'ds', 'Total Sales': 'y'})

        # Ensure required columns are present
        if 'ds' not in df.columns or 'y' not in df.columns:
            return HttpResponse("Error: DataFrame must have columns 'ds' and 'y'.")

        # Initialize Prophet model
        df_prophet = Prophet()

        # Fit the model
        df_prophet.fit(df)

        # Make future dataframe for predictions
        future = df_prophet.make_future_dataframe(periods=365 * 1, freq='D')

        # Make predictions
        forecast = df_prophet.predict(future)

        # Plot the forecast
        fig = df_prophet.plot(forecast, xlabel='Date', ylabel='Daily Revenue (Rs.)', figsize=(10, 6))
        plt.title('Daily Revenue Forecast')

        # Convert plot to image
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()

        # Embed the image in the HTML template
        graphic = base64.b64encode(image_png).decode('utf-8')

        return render(request, 'store/revenue_forecast.html', {'graphic': graphic})
