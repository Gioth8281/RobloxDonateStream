# Inspired by Akrow
# Import necessary libraries

from bs4 import BeautifulSoup
from roblox import Client

import roblox.utilities.exceptions
from secret import cookie
import browser_cookie3
import requests
import asyncio
import pytchat
import random
import time
import re


# Retrieve roblox user information
async def get_user(username, gamepass_id, user_created, price_limit):
    try:
        user = await client.get_user_by_username(username)
    except roblox.utilities.exceptions.UserNotFound:
        print(f"User {username.lower().capitalize()} doesn't exists..!")
        return None
    if user_created or not "None":
        user_created = user_created.split("-")
        usercreated_on_web = str(user.created.date()).split("-")
        user = user.id
        if user_created[0] > usercreated_on_web[0]:
            pass
        elif user_created[0] == usercreated_on_web[0]:
            if user_created[1] > usercreated_on_web[1]:
                pass
            elif user_created[1] == usercreated_on_web[1]:
                if user_created[2] > usercreated_on_web[2]:
                    pass
                elif user_created[2] == usercreated_on_web[2]:
                    pass
                else:
                    return None
            else:
                return None
        else:
            return None
    if gamepass_id is not None:
        gamepass_info = await get_gamepass_info(gamepass_id, username, price_limit, None)
        if gamepass_info:
            return gamepass_info
    else:
        gamepass_info = await get_gamepass_info(None, username, price_limit, user)
        if gamepass_info:
            return gamepass_info


# Retrieve gamepass information
async def get_gamepass_info(gamepass_id, username, price_limit, user):
    if gamepass_id is None:
        pattern = r'PlaceId=(\d+)'
        pattern2 = r"id=(\d+) .*? price=(\d+)"
        gamepass_id = []
        gamepasses_dict = {}

        response = requests.get(f"https://www.roblox.com/users/{user}/profile/")
        if response.status_code == 200:

            soup = BeautifulSoup(response.text, "html.parser")
            soup = soup.find("div", class_="game-grid")
            data = soup.find_all("div", class_="game-card-container")

            for place in data:
                if gamepass_id:
                    break

                place = place.find("a", class_="game-card-link")
                match = re.search(pattern, str(place))

                if match:
                    place = match.group(1)
                    place = await client.get_place(place)
                    place = place.universe
                    gamepasses = await place.get_gamepasses().flatten()
                    for gamepass in gamepasses:
                        match = re.search(pattern2, str(gamepass))
                        if match:
                            if int(match.group(2)) == int(price_limit):
                                gamepass_id.append(match.group(1))
                                break
                            elif int(match.group(2)) <= int(price_limit):
                                gamepasses_dict[match.group(1)] = match.group(2)
                else:
                    continue
            if len(gamepasses_dict.keys()) > 0 and not gamepass_id:
                limited_prices = {key: value for key, value in gamepasses_dict.items() if value <= price_limit}
                if limited_prices:
                    largest_value = max(limited_prices, key=limited_prices.get)
                    gamepass_id = largest_value
            elif gamepass_id:
                gamepass_id = gamepass_id[0]
            else:
                print(f"{username.lower().capitalize()}'s gamepasses are more expensive\nthan {price_limit} robux therefore I can't buy any of it!")
                return None
        else:
            return None

    response = requests.get(f"https://www.roblox.com/game-pass/{gamepass_id}")

    price_limit = price_limit.strip(", ")

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        try:
            gamepass_name = soup.find("h1").text
            button = soup.find("div", id="item-container")

            owner = soup.find("span", class_="text-label").text
            owner = owner.replace("By @", "")
            if owner.lower() == username.lower():
                try:
                    price = soup.find("span", class_="text-robux-lg wait-for-i18n-format-render").text
                except AttributeError:
                    return None
                if price:
                    if price_limit == "-1":
                        return [gamepass_name, button["data-product-id"], button["data-expected-seller-id"], button["data-expected-currency"], button["data-expected-price"], gamepass_id]
                    elif int(price) <= int(price_limit):
                        return [gamepass_name, button["data-product-id"], button["data-expected-seller-id"], button["data-expected-currency"], button["data-expected-price"], gamepass_id]
                    else:
                        print(f"{username.lower().capitalize()}'s gamepass {gamepass_id} is more\nexpensive than {price_limit} robux therefore I can't buy it!")
            else:
                print(f"{username.lower().capitalize()} isn't the owner of the gamepass {gamepass_id}!\n{owner.lower().capitalize()} is!")
        except Exception as e:
            print(e)
    return None


# Buys and deletes winner's gamepass
def buy_delete(gamepass_name, product_id, expected_seller_id, expected_currency, expected_price, gamepass_id, cookie):
    try:
        gamepass_name = gamepass_name.encode("UTF-8")
    except Exception:
        gamepass_name = "unnamed"
    try:
        session = requests.Session()
        session.cookies['.ROBLOSECURITY'] = cookie

        req = session.post(url='https://auth.roblox.com/')

        if 'X-CSRF-Token' in req.headers:
            session.headers['X-CSRF-Token'] = req.headers['X-CSRF-Token']

        # DELETE

        headers = {
            "Origin": "https://www.roblox.com",
            "Referer": f"https://www.roblox.com/game-pass/{gamepass_id}/{gamepass_name}",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Csrf-Token": session.headers['X-CSRF-Token'],
        }

        data = f"id={gamepass_id}"

        session.post(f"https://www.roblox.com/game-pass/revoke?id={gamepass_id}", headers=headers, data=data)

        # BUY

        headers = {
            "Origin": "https://www.roblox.com",
            "Referer": "https://www.roblox.com/",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Csrf-Token": session.headers['X-CSRF-Token'],
        }

        data = '{"expectedCurrency":' + expected_currency + ',"expectedPrice":' + expected_price + ',"expectedSellerId":' + expected_seller_id + '}'

        session.post(f"https://apis.roblox.com/game-passes/v1/game-passes/{product_id}/purchase", headers=headers, data=data)
        print("Successfully bought winner's gamepass!\nPlease check your Sales Of Goods :)")
    except Exception as e:
        print(e)


# Main function to keep it running
async def main(winner_limit):
    chat = pytchat.create(video_id=video_id)

    winners = {}
    while True:
        start_time = time.time()
        participants = {}
        print("You can now join the giveaway..!")
        while chat.is_alive():
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                break
            for c in chat.get().sync_items():
                # print(f"{c.datetime} [{c.author.name}]- {c.message}")
                text = c.message
                if text.lower().startswith("/join "):
                    text = text.lower().replace("/join ", "")
                    text = text.split(" ")
                    try:
                        if not text[0].lower().capitalize() in participants:
                            if text[0].lower() in winners:
                                if winners[text[0].lower()] > winner_limit:
                                    print(f"{text[0].lower().capitalize()} have already reached winning streak!")
                                    continue
                            try:
                                try:
                                    gamepass_info = await get_user(text[0], text[1], user_created, price_limit)
                                except roblox.utilities.exceptions.TooManyRequests:
                                    print("Too many requests,\nplease wait till the error\n is gone! Thank you!")
                                    continue
                            except IndexError:
                                try:
                                    gamepass_info = await get_user(text[0], None, user_created, price_limit)
                                except roblox.utilities.exceptions.TooManyRequests:
                                    print("Too many requests,\nplease wait till the error\n is gone! Thank you!")
                                    continue
                            if gamepass_info is not None:
                                print(f"Processing {text[0].lower().capitalize()}'s /join request! Price:{gamepass_info[4]}") 
                                participants[text[0].lower().capitalize()] = gamepass_info[0], gamepass_info[1], gamepass_info[2], gamepass_info[3], gamepass_info[4], gamepass_info[5]
                    except IndexError:
                        continue

        if participants:
            print("Winner is being selected...")
            await asyncio.sleep(5)
            winner = random.choice(list(participants.keys()))
            print(f"Winner is... {winner}!")
            if winner.lower() in winners:
                winners[winner.lower()] += 1
            else:
                winners[winner.lower()] = 1
            info = participants[winner.lower().capitalize()]
            buy_delete(info[0], info[1], info[2], info[3], info[4], info[5], cookie)
        else:
            print("Winner is being selected...")
            await asyncio.sleep(5)
            print(f"No one entered the giveaway..!?")
            await asyncio.sleep(2)


if __name__ == "__main__":
    #-  CONFIG  -#

    video_id = ""  # Just insert https://www.youtube.com/watch?v=dQw4w9WgXcQ the text after watch?v= of your livestream
    user_created = "None"  # Example 2024-01-31 or None
    price_limit = "3"  # Example 10 or -1 for infinite
    timeout = 200  # Example 120 for 2 minutes
    # cookie # Insert your cookie into secret.py or try running without the cookie
    winner_limit = 3  # How many wins can one get per stream

    #-  CONFIG ENDS HERE  -#

    if cookie == "":
        try:
            cookies = browser_cookie3.load(domain_name="roblox.com")
            cookies = str(cookies)
            cookie = cookies.split('.ROBLOSECURITY=')[1].split(' for .roblox.com/>')[0].strip()
        except Exception:
            print("I can't seem to get to your roblox cookie. Maybe try adding the roblox cookie manually.")
            exit()

    client = Client(cookie)
    asyncio.run(main(winner_limit))  # Run


"""
# PROGRAM UPDATE

I slightly improved the program I used on my streams. What has changed?

[+] Command ``/join username`` improved! It will automatically find the gamepass that has the highest price in accordance with the price limit.

[+] I changed the order of purchase and delete gamepass function. Now the first thing the program will do is try to delete the gamepass, and then buy it. That way it won't happen that I buy the gamepass I already own. So the gamepass wouldn't actually be bought.
"""
