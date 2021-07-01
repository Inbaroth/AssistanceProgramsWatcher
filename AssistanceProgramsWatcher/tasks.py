from time import sleep
from celery import shared_task
from bs4 import BeautifulSoup
import requests
from .models import AssistanceProgram, EligibleTreatment


# HWF = healthwellfoundation
# url don't really change over time so for now we'll leave it hard-coded
HWF_url = "https://www.healthwellfoundation.org/disease-funds/"


def get_soup(url):
    req = requests.get(url)
    return BeautifulSoup(req.content, 'html.parser')


def get_hwf_funds(soup):
    return soup.find('main', attrs={'id': 'main'}).find('div', attrs={'class': 'subsection narrow'}).find('ul', attrs={'class': 'funds'})


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
    fund_soup = get_soup(fund_url)
    details_div = get_fund_details(fund_soup)
    return get_fund_treatments(details_div)


# <name, url, status(open/close)> dict
def iterate_and_operate(funds_ul, fund_operate):
    for li in funds_ul.find_all('li'):
        fund = {'name': li.text, 'url': li.find('a')['href'], 'status': li['data-status']}
        fund = get_final_fund_data(fund)
        print(fund)
        fund_model_instance = fund_operate(fund)
        treatment_l = get_fund_treatments_data(fund['url'])
        for treatment in treatment_l:
            treatment_model_instance = create_or_update_treatment(treatment)
            fund_model_instance[0].treatments.add(treatment_model_instance[0])


# assumption: if invalid status - will be close
def convert_to_bool(status):
    if status == 'open':
        return True
    else:
        return False


def create_fund(fund):
    return AssistanceProgram.objects.create(name=fund['name'],
                                            status=convert_to_bool(fund['status']),
                                            grant_amount=fund['grant_amount'],
                                            url=fund['url'])
    # sleep few seconds to avoid database block
    sleep(5)


# TODO: enhancement - validate currency to make sure only legal currency signs are inseted
def get_currency(grant_amount_str):
    return grant_amount_str[0]


def get_int_amount(grant_amount_str):
    try:
        return int(grant_amount_str[1:].replace(',', ''))
    except ValueError:
        return 0


def create_or_update_fund(fund):
    # If AssistanceProgram exists with name=fund['name'] then update with rest of data
    # Else create new AssistanceProgram

    return AssistanceProgram.objects.update_or_create(
        name=fund['name'],
        defaults={'status': convert_to_bool(fund['status']),
                  'grant_amount': get_int_amount(fund['grant_amount']),
                  'currency': get_currency(fund['grant_amount']),
                  'url': fund['url']})


def create_or_update_treatment(treatment):
    return EligibleTreatment.objects.get_or_create(name=treatment)
    # sleep few seconds to avoid database block
    sleep(5)


@shared_task
def create_or_update_program_treatment():
    print('creating program data')
    soup = get_soup(HWF_url)
    funds_main = get_hwf_funds(soup)
    iterate_and_operate(funds_main, create_or_update_fund)


while True:
    create_or_update_program_treatment()
    # updating data every 15 seconds
    sleep(15)
