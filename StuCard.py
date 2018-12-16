import getpass
import re

import requests
from bs4 import BeautifulSoup


class Contest:
    base_url = "https://www.stucard.ch"

    def __init__(self, name, url, contest_id, session):
        self.name = name
        self.url = url
        self.id = contest_id
        self.session = session

    def participate(self):
        url = "{}/?wettbewerb=1&participate={}".format(self.base_url, self.id)
        response = self.session.get(url)
        return response

    def has_participated(self):
        url = self.base_url + self.url
        response = self.session.get(url)
        return "wettTeilnahmeOk" in response.text

    def __str__(self):
        return "{}: url=\"{}\", id={}".format(self.name, self.base_url + self.url, self.id)


def login(email, password):
    print("Logging in with {}.".format(email))
    login_post = {"loginEmail": email,
                  "loginPassword": password}

    url = "https://www.stucard.ch/?loginMember=1&keepPage=1"
    s = requests.Session()
    r = s.post(url, data=login_post)
    if r.status_code != 200:
        print("Login unsuccessful")
        return None
    print("Login successful!")
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
    print("Welcome to the Stu Card contest participator!")
    logged_in = False
    login_session = None

    while not logged_in:
        email = input("Whats your StuCard mail?")
        passwd = getpass.getpass("whats your StuCard password?")

        login_session = login(email, passwd)

        # Login successful
        if login_session != None:
            logged_in = True
        else:
            print("I'm sorry, but I can't log in with these credentials. Please try again.")

    contests = get_contests(login_session)

    count = 0
    for contest in contests:
        if not contest.has_participated():
            contest.participate()
            print("Participating in {}".format(contest.name))
            count += 1
    print("Participated in {} new contests.".format(count))
    print("Now participating in a total of {} contests".format(len(contests)))
