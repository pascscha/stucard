import getpass
import re
import sys

import requests
from bs4 import BeautifulSoup
from coloring import *


class Contest:
    base_url = "https://www.stucard.ch"
    participation_file = "participated_contests.txt"

    def __init__(self, name, url, contest_id, session):
        self.name = name
        self.url = url
        self.id = contest_id
        self.session = session

    def participate(self):
        # Participate
        url = "{}/?wettbewerb=1&participate={}".format(self.base_url, self.id)
        self.session.get(url)

        # Check if we succeeded
        url = self.base_url + self.url
        response = self.session.get(url)
        if "wettTeilnahmeOk" in response.text:
            with open(self.participation_file, "a+") as f:
                f.write(self.id + "\n")
            return True
        else:
            return False

    def has_participated(self):
        with open(self.participation_file, "r+") as f:
            participated = self.id+"\n" in f.readlines()
        return participated

    def __str__(self):
        return "{}, {}, {}".format(self.name, self.base_url + self.url, self.id)


def login(email, password):
    print("Logging in with {}".format(email), end="")
    login_post = {"loginEmail": email,
                  "loginPassword": password}

    url = "https://www.stucard.ch/?loginMember=1&keepPage=1"
    s = requests.Session()
    r = s.post(url, data=login_post)
    if r.status_code != 200:
        return None
    print(colorize(" - {FG_GREEN}Success!{FG_DEFAULT}"))
    return s


def get_contests(session):
    out = []
    response = session.get("https://www.stucard.ch/de/wettbewerb/")
    soup = BeautifulSoup(response.text, 'html.parser')
    block_container = soup.find("div", {"id": "blockContainer1"})
    blocks = block_container.find_all("div", {"class": re.compile("item.*")})
    for block in blocks:
        title = block.text.replace("\n", " ").replace("   CLICK & WIN  ", "")
        tease = block.find("div", {"class": "dealBlockTease"})
        url = tease['data-url']
        contest_id = tease['id'].replace("dealTease", "")
        out.append(Contest(title, url, contest_id, session))
    return out


if __name__ == "__main__":

    if len(sys.argv) == 3:
        email = sys.argv[1]
        passwd = sys.argv[2]
        login_session = login(email, passwd)
        if login_session == None:
            print(colorize("\n{FG_RED}The provided credentials are invalid.{FG_DEFAULT}"))
            exit(1)

    else:
        show_tag("tag.txt")

        with open("welcome.txt", "r") as f:
            welcome_text = f.read()

        welcome_text = colorize(welcome_text)

        print()
        print(welcome_text)
        print()

        logged_in = False
        login_session = None

        while not logged_in:
            email = input(colorize("Enter your {FG_BLUE}Stu{FG_GREEN}Card{FG_DEFAULT} mail address: "))
            passwd = getpass.getpass(colorize("Enter your {FG_BLUE}Stu{FG_GREEN}Card{FG_DEFAULT} password: "))

            print()

            login_session = login(email, passwd)

            # Login successful
            if login_session != None:
                logged_in = True
            else:
                print(colorize(
                    "\n{FG_RED}I'm sorry, but I can't log in with these credentials. Please try again.{FG_DEFAULT}\n"))

    print("Fetching Contests", end="")
    contests = get_contests(login_session)
    print(colorize(" - {FG_GREEN}Done{FG_DEFAULT}"))

    print("Check for Contests you haven't participated in yet.")
    count = 0
    for contest in contests:
        if not contest.has_participated():
            contest.participate()
            print("\tParticipating in {}".format(contest.name))
            count += 1
    if count > 0:
        print("\nNewly participating in {} contests.".format(count))
    else:
        print("Already participating in all contests :)")
    print("You are currently participating in a total of {} contests".format(len(contests)))
