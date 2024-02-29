import openai
import os
from dotenv import load_dotenv
import json
from twilio.rest import Client
import re
import uuid
import qrcode
import copy
from google.cloud import bigquery
import ast


project_id = 'ck-eams'

# Initialize a BigQuery client
client = bigquery.Client(project=project_id)
load_dotenv()

api_key = os.getenv("API_KEY")
openai.api_key = api_key


context = [ {'role':'system', 'content':"""
You are OrderBot, an automated service to collect orders for restaurants. \
Your  goal is to place orders and explain the users about the food items in your menu. \
you can also recommend the best food items whenever needed \
You should respond only to take the orders and for all other queries you should not respond since you are an orderbot. \
You first greet the customer as 'Hello I am an orderbot', and then collect the order.\
ask if they want to add anything else to their order \
You wait to collect the entire order, then summarize it, all amount are in /- \
Make sure to clarify all options, extras  uniquely \
identify the item from the menu.\
If the item ordered by the user does not match with any item in the menu, then ask the user to check and re-enter the name of the item in a polite manner. \
If the item ordered by the user nearly matches with any one item in the menu , then provide the matched item names in the menu to the user and ask the user politely to confirm the item name to order \ 
If the name of item ordered by the user matches with more than one item in the menu, then ask the user to check and re-enter the correct item name as per the menu he/she wants in a polite manner or you have to suggest the matching item names and then ask the user to  choose the item \
You should respond in a short and  very conversational friendly style. \
As an orderbot it is your strict responsibility to store the orders when prompted . This is very important task of yours\
You should not tell that no order is found in the chat, even if the  user has already ordered some items \
You have to store multiple items in a single order , if ordered \
Do not ask the user everytime whether he/she want it for pickup or delivery. \
If the user wants or seems to add nothing to order, then tell him the summary of items he/she has ordered, and then ask the user to confirm by asking the user to type 'confirm'\
Only if the user types 'confirm', then only ask the user whether the user want it for 'pickup' or 'delivery' and also ask the  user to type 'pickup' or 'delivery' to successfully place the order\
At last,if the user enters 'pickup' or 'delivery', tell the user that his/her order is placed succesfully and then you should prompt the user to click on place order button to view their order and  make their payment \
You should take orders only for the items that are included in the following menu. \
Tell all the available items to the user for particular categories like "Veg Starters" , "Soups-Veg" , "Soups - Non Veg"   if asked \
You should cross check the names of items present in the menu . If item ordered by the user matches partially then ask the user to enter the name of item completely as per the menu in a polite manner .\
The menu includes \

Combos
Haveli Special Kulcha with Chana Combo (CHEF'S SPECIAL): 299 /-
Gobhi Kulcha with Chana Combo: 249 /-
Mixed Veg Kulcha with Chana Combo: 279 /-
Onion Kulcha with Chana Combo: 279 /-
Paneer Kulcha with Chana Combo: 299 /-
Stuffed Cheese Kulcha with Chana Combo: 359 /-
Stuffed Aloo Kulcha with Chana Combo: 259 /-
Garlic Kulcha with Chana Combo: 209 /-

Soups
Sweet Corn Soup: 239 /-
Veg Clear Soup: 239 /-
Cream of Tomato Soup: 239 /-
Hot & Sour Soup: 239 /-
Manchow Soup: 239 /-
Talumain Soup: 239 /-
Lemon Coriander Soup: 239 /-

Salad
Green Salad [200 grams]: 169 /-

Starters
Haveli Paneer Tikka [8 Pieces] (CHEF'S SPECIAL): 429 /-
Achari Paneer Tikka [8 Pieces]: 409 /-
Stuffed Paneer Tikka [8 Pieces]: 469 /-
Malai Paneer Tikka [8 Pieces]: 429 /-
Haryali Paneer Tikka [8 Pieces]: 429 /-
Haveli Mushroom Tikka [12 Pieces] (CHEF'S SPECIAL): 429 /-
Achari Mushroom Tikka [12 Pieces]: 409 /-
Stuffed Mushroom Tikka [8 Pieces]: 409 /-
Veg Seekh Kebab [4 Pieces]: 429 /-
Malai Broccoli [8 Pieces]: 459 /-
Soya Malai Chaap (8 Pieces]: 429 /-
Soya Achari Chaap [8 Pieces]: 429 /-
Afghani Chaap: 429 /-
Soya Cheese Chaap: 429 /-
Hara Bhara Kebab [8 Pieces]: 429 /-
Dragon Paneer: 419 /-
Thai Basil Paneer: 429 /-
Mushroom Black Pepper: 449 /-
Thai Pepper Corn Cheese Roll: 479 /-
Water Cashew Nut in Hot Garlic Sauce: 449 /-
Stuffed Golden Fry Mushroom: 479 /-
Stuffed Thai Basil Paneer Tikka: 479 /-
Kaju Creamy Tikki Kebab: 479 /-
Makki Malai Seekh Kebab: 449 /-
Beetroot Cheese Tikki Kebab: 479 /-

Main Course
Haveli Special Black Dal Fry (CHEF'S SPECIAL): 539 /-
Dal Makhani: 429 /-
Yellow Dal: 369 /-
Yellow Dal Fry: 379 /-
Haveli Special Paneer (CHEF'S SPECIAL): 489 /-
Paneer Tikka Butter Masala: 429 /-
Paneer Lababdar: 429 /-
Kadhai Paneer: 429 /-
Paneer Bhurji: 429 /-
Palak Paneer: 409 /-
Shahi Paneer: 409 /-
Tomato Paneer: 409 /-
Matar Paneer: 409 /-
Paneer Makhani: 419 /-
Paneer Pasanda: 419 /-
Mix Veg: 379 /-
Roasted Mushroom Masala: 419 /-
Mushroom Do Pyaza: 409 /-
Palak Mushroom: 409 /-
Mushroom Matar Masala: 419 /-
Gobhi Aloo Masala: 379 /-
Chana Masala: 379 /-
Rajma Masala: 379 /-
Cheese Butter Masala: 489 /-
Malai Kofta: 419 /-
Punjabi Kofta: 419 /-
Jeera Aloo: 379 /-
Dum Aloo: 379 /-
Veg Kolhapuri: 399 /-
Paneer Methi Chaman: 449 /-
Paneer Khurchan: 449 /-
Kaju Paneer Masala: 479 /-
Vegetable Diwani Handi: 429 /-
Soya Shahi Chaap Gravy: 429 /-
Paneer Chatnar: 429 /-
Soya Chaap Lababdar: 399 /-
Makhani Paneer Bhurji: 449 /-
Kaju Tomato: 449 /-
Mix Veg Bharta: 389 /-

Breads
Aloo Paratha (Served with curd): 249 /-
Gobi Paratha (Served with curd): 249 /-
Paneer Paratha (Served with curd): 299 /-
Tandoori Roti: 59 /-
Tandoori Butter Roti: 169 /-
Plain Naan: 99 /-
Butter Naan: 109 /-
Lachha Paratha: 109 /-
Lal Mirch Paratha: 109 /-
Hari Mirch Paratha: 109 /-
Methi Paratha: 109 /-
Missi Roti: 199 /-
Garlic Naan: 119 /-
Chur Chur Naan: 229 /-
Plain Tawa Roti: 59 /-
Tawa Butter Roti: 69 /-
Tawa Plain Paratha: 79 /-
Aloo Tawa Paratha: 139 /-
Gobhi Tawa Paratha: 159 /-
Paneer Tawa Paratha: 169 /-
Rumali Roti: 79 /-
Missi Onion Roti: 119 /-
Cheese Naan: 219 /-
Kashmiri Naan: 219 /-

Rice & Biryani
Plain Rice: 219 /-
Jeera Rice: 239 /-
Veg Pulao: 359 /-
Matar Pulao: 359 /-
Kashmiri Pulao: 479 /-
Plain Khichdi: 339 /-
Masala Khichdi: 359 /-
Veg Biryani: 359 /-

Chinese
Chilli Paneer Dry: 409 /-
Chilli Paneer Gravy: 420 /-
Garlic Paneer: 379 /-
Schezwan Paneer Dry: 429 /-
Paneer 65: 429 /-
Gobhi 65: 359 /-
Veg Manchurian Dry: 409 /-
Veg Manchurian Gravy: 419 /-
Veg Crispy: 319 /-
Chilli Mushroom Dry: 429 /-
Chilli Potato: 319 /-
Honey Chilli Potato: 379 /-
Honey Chilli Cauliflower: 379 /-
Chilli Soyabean: 379 /-
Chilli Soya Chaap: 429 /-
Crispy Corn: 429 /-
Crispy Baby Corn in Hot Chilly Sauce: 429 /-
Vegetables in Sweet & Sour Sauce: 409 /-

Fried Rice
Paneer Schezwan Fried Rice: 379 /-
Schezwan Fried Rice: 379 /-
Fried Rice: 379 /-

Noodles
Veg Chowmein: 359 /-
Veg Schezwan Chowmein: 379 /-
Veg Hakka Noodles: 359 /-
Veg Chopsuey: 379 /-
Cheese Garlic Noodles: 399 /-
Chinese Chopsuey: 429 /-

Snacks
Paneer Pakoda [8 Pieces]: 379 /-
Assorted Pakoda [12 Pieces]: 319 /-
French Fries [250 grams]: 279 /-
Masala Fries [250 grams]: 319 /-
Paneer Kulcha: 229 /-
Masala Kulcha: 229 /-
Onion Kulcha: 199 /-
Chinese Bhel: 359 /-
Spring Roll: 319 /-

Accompaniments
Roasted Papad: 79 /-
Fry Papad: 79 /-
Masala Papad: 129 /-
Amritsari Masala Papad: 189 /-
Pineapple Raita [300 grams]: 279 /-
Mixed Veg Raita [300 grams]: 249 /-
Boondi Raita [300 grams]: 219 /-

Desserts
Gulab Jamun [2 Pieces]: 169 /-
Moong Dal Halwa [200 grams]: 279 /-
Vanilla Ice Cream: 169 /-
Strawberry Ice Cream: 169 /-
Mango Ice Cream: 189 /-
Butterscotch Ice Cream: 189 /-
Tutti Frutti Ice Cream [2 Scoop]: 189 /-
Chocolate Ice Cream [2 Scoop]: 189 /-
Caramel Nut Ice Cream [2 Scoop]: 219 /-

Drinks (Beverages)
Milk Tea: 59 /-
Desi Masala Tea: 159 /-
Special Gur Tea: 169 /-
Coffee: 109 /-
Maharaja Lassi: 319 /-
Amritsari Sweet Lassi: 169 /-
Amritsari Salted Lassi: 169 /-
Mango Lassi: 229 /-
Fresh Lime Soda: 199 /-
Iced Tea Lemon & Peach: 279 /-
Haveli Classic Mojito (Non alcoholic): 299 /-
Green Apple Mojito (Non alcoholic): 279 /-
Kiwi Lagoon: 279 /-
Blue Moon: 279 /-
Almond Blast: 219 /-
Mango Masti: 219 /-
Oreo Shake: 219 /-
Coffee Shake: 219 /-
Rosie Rose: 219 /-
Strawberry: 219 /-
Brownie Blast: 249 /-
Fruit Punch: 249 /-
Haveli Special Cold Coffee (CHEF'S SPECIAL): 279 /-
Blended Cold Coffee: 299 /-
Iced Cold Coffee: 299 /-
Fantisimo: 319 /-
Choco Sparkle: 319 /-
Jungle Java: 359 /-

"""
} 
]

user_conversations={}

def get_completion_from_messages1(messages, model="gpt-3.5-turbo-0125", temperature=0.5):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, # this is the degree of randomness of the model's output
    )

    return response.choices[0].message["content"]

def add_user_message(user_id, message):
    if user_id not in user_conversations:
        context_copy = copy.deepcopy(context)
        user_conversations[user_id] = context_copy
    user_conversations[user_id].append({"role": "user", "content": message})


# Function to get the conversation history for a user
def get_user_conversation(user_id):
    return user_conversations.get(user_id, [])


def collect_messages_text1(msg,user_id):
    prompt=msg
    # print(user_conversations)
    add_user_message(user_id, msg)
    
    conversation = get_user_conversation(user_id)
    response = get_completion_from_messages1(conversation)
    
    user_conversations[user_id].append({"role": "assistant", "content": response})
    
    if(prompt=="pickup" or prompt=="delivery"):
        store_order_summary(user_id)
    return response


def store_order_summary(user_id):
    msg="get all the details of items ordered by the user from the chat and provide the order details in a python list containing tuples where each tuple contains item_name,quantity and price. here price is the price of each item. If once 'pickup' is prompted,  then don't add previous ordered items in the current order. please make sure this works correctly else it creates huge errors in billing. Don't include every item present in the chat. Include only items that are actually ordered by the user in the ordered list . please do it carefully "
    add_user_message(user_id, msg)
    conversation = get_user_conversation(user_id)
    response = get_completion_from_messages1(conversation)
    user_conversations[user_id].append({"role": "assistant", "content": response})
    
    # Regular expression pattern to match a list of tuples
    pattern = r'\[.*?\]'

    # Use re.findall to extract all matching patterns
    matches = re.findall(pattern, response,re.DOTALL)
    extracted_list = []
    # Convert the matched string to a Python list of tuples
    if matches:
        extracted_list = eval(matches[0])  # Use eval to convert the string to a list
        print(extracted_list)
    

        id=user_id
        # Insert data into the table
        for data in extracted_list:
                item_name, quantity, price = data
                print(item_name, quantity, price) 
                sql_query="""
                    INSERT INTO ck-eams.dosabot.order_items(id, item_name, quantity, price)
                    VALUES (@id,@item_name,@quantity,@price)"""

                job_config = bigquery.QueryJobConfig(
                        query_parameters=[
                            bigquery.ScalarQueryParameter("id", "STRING", id),
                            bigquery.ScalarQueryParameter("item_name", "STRING", item_name),
                            bigquery.ScalarQueryParameter("quantity", "STRING", quantity),
                            bigquery.ScalarQueryParameter("price", "STRING", price)
                        ]
                    )

                # Run the query job
                query_job = client.query(sql_query, job_config=job_config)

                # Wait for the job to complete (optional)
                query_job.result()
                for row in query_job.result():
                    print(row)
    else:
        print("No order details found in the text. Can you please order again.")    
    # user_phone_number = '+916302211930'  # Replace with the user's phone number
    # send_whatsapp_message(user_phone_number, order_filename)



def send_whatsapp_message(to, body):
    # Twilio credentials
    twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER") # Twilio's sandbox WhatsApp number

    client = Client(twilio_account_sid, twilio_auth_token)
    
    with open("order_summary.json","r") as res:
        result=res.read()

    try:
        users=['+916302211930','+919347665827']
        for i in users:
            message = client.messages.create(
                from_=twilio_whatsapp_number,
                to='whatsapp:'+i,
                body="Your order has been placed successfully.\n\n"+result+"\n\nThank you and Visit Again!!!"
            )

        print('WhatsApp message sent successfully.')
        print(message.sid)
    except Exception as e:
        print('Error sending WhatsApp message:', str(e))


def payment(user_id):
    upi_id = "7013049899@ybl"   #Dosa owner UPI
    note = "Payment for your order"   #List of items ordered by customer
    id=user_id
    sql_query="""SELECT total_price 
        FROM ck-eams.dosabot.orders 
        WHERE id = @id
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("id", "STRING",id),
        ])

        # Run the query job
    query_job = client.query(sql_query, job_config=job_config)
    money_value=[row[0] for row in query_job.result()]

    # Formulate UPI URL
    upi_url = f"upi://pay?pa={upi_id}&pn=&mc=&tid=&tr=&tn={note}&am={money_value[0]}&cu=INR"

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_url)
    qr.make(fit=True)

    # Create and save QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    # qr_img.save("static/upi_qr_code.png")
    qr_img.save(f"static/upi_qr_code_{user_id}.png")
     
