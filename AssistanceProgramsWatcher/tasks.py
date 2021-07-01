from time import sleep
from celery import shared_task
from bs4 import BeautifulSoup
import requests
from .models import AssistanceProgram, EligibleTreatment


# HWF = healthwellfoundation
# url don't really change over time so for now we'll leave it hard-coded
HWF_url = "https://www.healthwellfoundation.org/disease-funds/"


def get_soup(url):
    try:
        res = requests.get(url)
        retry = 0
    except requests.exceptions.HTTPError as e:
        print(e.__str__())
        return  # the scraper will try again
    except requests.exceptions.ConnectionError as e:
        if retry < 10:
            print("connection error, retrying to connect..")
            get_soup(url)
        else:
            print(e.__str__())
            return
    return BeautifulSoup(res.content, 'html.parser')


def get_hwf_funds(soup):
    try:
        return soup.find('main', attrs={'id': 'main'}).find('div', attrs={'class': 'subsection narrow'}).find('ul', attrs={'class': 'funds'})
    except Exception as e:
        print(e.__str__())
        return None


def get_fund_details(soup):
    return soup.find('div', attrs={'id': 'fund-details'})


def extract_amount(text, prefix_chars, suffix_chars):
    text = remove_prefix(text, prefix_chars)
    text = remove_suffix(text, suffix_chars)
    return text.strip()


def remove_prefix(text, position_chars):
    return text[text.find(position_chars)+len(position_chars):]


def remove_suffix(text, position_chars):
    return text[:text.find(position_chars)]


def get_fund_grant_amount(soup):
    fund_details_div = soup.find('div', attrs={'class': 'details'})
    maximum_award_level_div = fund_details_div.find_all('div', attrs={'class': 'row clearfix'})[1].find('div')
    return extract_amount(str(maximum_award_level_div), '</h4>', '</div>')


# return list of <name, url, status(open/close), grant_amount> dicts
def get_final_fund_data(fund):
    fund_soup = get_soup(fund['url'])
    details_div = get_fund_details(fund_soup)
    grant_amount = get_fund_grant_amount(details_div)
    fund.update({'grant_amount': grant_amount})
    return fund


def get_fund_treatments(soup):
    treatments_covered_div = soup.find('div', attrs={'class': 'treatments-covered'})
    treatments_div = treatments_covered_div.find('div', attrs={'class': 'treatments'})
    return [li.text for li in treatments_div.find_all('li')]


def get_fund_treatments_data(fund_url):
    try:
        fund_soup = get_soup(fund_url)
        details_div = get_fund_details(fund_soup)
        return get_fund_treatments(details_div)
    except Exception:
        return None


# <name, url, status(open/close)> dict
def iterate_and_operate(funds_ul, fund_operate, treatments_operate):
    try:
        all_li = funds_ul.find_all('li')
    except Exception as e:
        print(e.__str__())
        return

    for li in all_li:
        fund = {'name': li.text, 'url': li.find('a')['href'], 'status': li['data-status']}
        fund = get_final_fund_data(fund)
        print("trying to insert:")
        print(fund)
        fund_model_instance = fund_operate(fund)
        # sleep few seconds to avoid database block
        sleep(5)
        if fund_model_instance is not None:
            treatment_l = get_fund_treatments_data(fund['url'])   # asumption: we are ok with having data only about program and not about the treatments avilable in this program
            if treatment_l is not None:
                for treatment in treatment_l:
                    treatment_model_instance = treatments_operate(treatment)
                    # sleep few seconds to avoid database block
                    sleep(5)
                    if treatment_model_instance is not None:
                        fund_model_instance[0].treatments.add(treatment_model_instance[0])


# assumption: if invalid status - will be close
def convert_to_bool(status):
    if status == 'open':
        return True
    else:
        return False


def create_fund(fund):
    try:
        return AssistanceProgram.objects.create(name=fund['name'],
                                                status=convert_to_bool(fund['status']),
                                                grant_amount=fund['grant_amount'],
                                                url=fund['url'])
    except Exception as e:
        print(e.__str__())
        return None


# TODO: enhancement - validate currency to make sure only legal currency signs are instead
def get_currency(grant_amount_str):
    return grant_amount_str[0]


# assumption: if the total amount data is invalid - we'll have default value 0
def get_int_amount(grant_amount_str):
    try:
        return int(grant_amount_str[1:].replace(',', ''))
    except ValueError:
        return 0


# we don't allow partial program data
def is_valid(fund):
    if None in fund.values():
        return False


def create_or_update_fund(fund):
    # If AssistanceProgram exists with name=fund['name'] then update with rest of data
    # Else create new AssistanceProgram
    if is_valid(fund):
        try:
            return AssistanceProgram.objects.update_or_create(
                name=fund['name'],
                defaults={'status': convert_to_bool(fund['status']),
                          'grant_amount': get_int_amount(fund['grant_amount']),
                          'currency': get_currency(fund['grant_amount']),
                          'url': fund['url']})
        except Exception as e:
            print(e.__str__())
    else:
        return None


def create_or_update_treatment(treatment):
    try:
        return EligibleTreatment.objects.get_or_create(name=treatment)
    except Exception as e:
        print(e.__str__())
        return None


@shared_task
def create_or_update_program_treatment():
    print('creating program data')
    try:
        soup = get_soup(HWF_url)
        if soup is not None:
            funds_main = get_hwf_funds(soup)
            if funds_main is not None:
                iterate_and_operate(funds_main, create_or_update_fund, create_or_update_treatment)
    except Exception as e:
        return


while True:
    # the web scraper continuously running
    create_or_update_program_treatment()
    # updating data every 15 seconds, the API will be updated by refreshing
    sleep(15)
