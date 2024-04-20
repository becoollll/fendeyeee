from flask import Flask, render_template, request, jsonify
import pandas as pd
import psycopg2

app = Flask(__name__)

# Update these variables with your PostgreSQL database details
db_host = 'localhost'
db_port = '5432'
db_user = 'wilson'
db_password = 'qwert'
db_name = 'foundation'

# Establish a connection to the PostgreSQL database
connection = psycopg2.connect(host=db_host, port=db_port, user=db_user, password=db_password, database=db_name)

# Read the data from PostgreSQL into a DataFrame
query = "SELECT * FROM items"
df = pd.read_sql_query(query, connection)

# Define the items table
items_query = "SELECT * FROM items"
items_df = pd.read_sql_query(items_query, connection)

# Define the records table
records_query = "SELECT * FROM records"
records_df = pd.read_sql_query(records_query, connection)

# Close the database connection
connection.close()

# get brands
brands = df['brand'].unique()

@app.route('/')
def index():
    return render_template('index.html', brands=brands)

@app.route('/new')
def new():
    return render_template('new.html', brands = brands)

@app.route('/introduction')
def introduction():
    return render_template('introduction.html', brands = brands)

@app.route('/find_page')
def find_page():
    return render_template('find.html', brands = brands)

@app.route('/get_names', methods=['POST'])
def get_names():
    selected_brand = request.form['selected_brand']
    brand_df = df[df['brand'] == selected_brand]
    names_for_brand = brand_df['name'].unique()

    if len(names_for_brand) == 1:
        # if brand only has one product, then choose colors directly
        name_df = df[(df['brand'] == selected_brand) & (df['name'] == names_for_brand[0])]
        colors_for_name = name_df['color'].unique()
        return {'names': names_for_brand.tolist(), 'colors': colors_for_name.tolist()}
    else:
        return {'names': names_for_brand.tolist()}

@app.route('/get_colors', methods=['POST'])
def get_colors():
    selected_brand = request.form['selected_brand']
    selected_name = request.form['selected_name']
    name_df = df[(df['brand'] == selected_brand) & (df['name'] == selected_name)]
    colors_for_name = name_df['color'].unique()
    return {'colors': colors_for_name.tolist()}

@app.route('/get_item_info', methods=['POST'])
def get_item_info():
    selected_brand = request.form['selected_brand']
    selected_name = request.form['selected_name']
    selected_color = request.form['selected_color']

    item_info = df[(df['brand'] == selected_brand) & (df['name'] == selected_name) & (df['color'] == selected_color)].to_dict('records')

    return jsonify(item_info)

@app.route('/get_next_group_id', methods=['GET'])
def get_next_group_id():
    # Query the maximum group_id from the records table
    query = "SELECT MAX(group_id) FROM records"
    connection = psycopg2.connect(host=db_host, port=db_port, user=db_user, password=db_password, database=db_name)
    cursor = connection.cursor()
    cursor.execute(query)
    max_group_id = cursor.fetchone()[0]
    connection.close()

    # Calculate the next group_id
    next_group_id = max_group_id + 1 if max_group_id is not None else 1

    return jsonify({'next_group_id': next_group_id})


@app.route('/add', methods=['POST'])
def add():
    if request.method == 'POST':
        group_id = int(request.form['group'])
        brands = request.form.getlist('brand[]')
        names = request.form.getlist('name[]')
        colors = request.form.getlist('color[]')



        # Establish a connection to the PostgreSQL database
        connection = psycopg2.connect(host=db_host, port=db_port, user=db_user, password=db_password, database=db_name)
        cursor = connection.cursor()

        try:
            # Loop through the selected products and insert them into the records table
            for brand, name, color in zip(brands, names, colors):
                # Fetch item_id from the items table
                item_query = f"SELECT id FROM items WHERE brand = '{brand}' AND name = '{name}' AND color = '{color}'"
                cursor.execute(item_query)
                item_id = cursor.fetchone()[0]

                print(item_id)
                print(type(item_id), type(group_id))
                # Insert data into the records table
                records_query = f"INSERT INTO records (group_id, item_id) VALUES ({group_id}, {item_id})"
                cursor.execute(records_query)
                print(f"Inserted data for brand={brand}, name={name}, color={color}")
            # Commit the changes to the database
            connection.commit()
            print("Products added successfully!")
            return "Products added successfully!"

        except Exception as e:
            # Handle any exceptions and rollback the transaction
            connection.rollback()
            print(f"Error: {str(e)}")
            return f"Error: {str(e)}"

        finally:
            # Close the database connection
            connection.close()

    return render_template('add.html')

@app.route('/get_dropdown_data', methods=['GET'])
def get_dropdown_data():
    return {
        'brands': brands.tolist(),
        'names': items_df['name'].unique().tolist(),
        'colors': items_df['color'].unique().tolist()
    }


@app.route('/get_group_info', methods=['POST'])
def get_group_info():
    selected_brand = request.form['brand']
    selected_name = request.form['name']
    selected_color = request.form['color']

    # Fetch item_id from the items table
    item_query = f"SELECT id, brand, name, type, color, makeup FROM items WHERE brand = '{selected_brand}' AND name = '{selected_name}' AND color = '{selected_color}'"
    connection = psycopg2.connect(host=db_host, port=db_port, user=db_user, password=db_password, database=db_name)
    cursor = connection.cursor()
    cursor.execute(item_query)
    selected_product = cursor.fetchone()

    # If there is no data for the selected product, display a message
    if not selected_product:
        connection.close()
        return "<h2>NO DATA</h2>"

    selected_item_id, brand, name, product_type, color, makeup = selected_product

    # Fetch all group_ids for the selected item_id
    group_query = f"SELECT group_id FROM records WHERE item_id = {selected_item_id}"
    cursor.execute(group_query)
    group_ids = [group[0] for group in cursor.fetchall()]

    # If there are no group_ids, display a message
    if not group_ids:
        connection.close()
        return "<h2>NO DATA</h2>"

    # Fetch details from the items table for all item_ids in the group_ids
    group_items_query = f"SELECT records.group_id, items.* FROM items JOIN records ON items.id = records.item_id WHERE records.group_id IN ({','.join(map(str, group_ids))})"
    cursor.execute(group_items_query)
    group_items_data = cursor.fetchall()

    connection.close()

    # Organize data by group_id
    grouped_data = {}
    for item_data in group_items_data:
        group_id = item_data[0]
        item_details = item_data[1:]

        if group_id not in grouped_data:
            grouped_data[group_id] = []

        grouped_data[group_id].append(item_details)

    # Display the selected product information
    product_info = f'<div class="center"><h2 class="show_ti">你選的粉底是</h2>'
    product_info += f'<p class="show_it">品牌 | {brand}</p>'
    product_info += f'<p class="show_it">產品 | {name}</p>'
    product_info += f'<p class="show_it">色號 | {color}</p>'
    product_info += f'<p class="show_it">種類 | {product_type}</p></div>'

    # Display the group information sorted by group_id in ascending order
    group_info = "<h2>相似色號粉底液有</h2>"
    for group_id in sorted(grouped_data.keys()):
        items_in_group = grouped_data[group_id]
        group_info += f"<h3>USER {group_id}</h3><ul>"
        for item_details in items_in_group:
            group_info += f"<li>ID: {item_details[0]}, Brand: {item_details[1]}, Name: {item_details[2]}, Type: {item_details[3]}, Color: {item_details[4]}, Makeup: {item_details[5]}</li>"
        group_info += "</ul>"

    return product_info + group_info

if __name__ == '__main__':
    app.run(debug=True)
