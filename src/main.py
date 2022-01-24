from dataclasses import dataclass
from typing import List
import gspread
from operator import attrgetter
import time
import logging

logging.basicConfig(filename='botlog.log', level=logging.INFO, format='%(asctime)s %(levelname)s - %(message)s',\
    datefmt='%d/%m/%Y %I:%M:%S %p')
url = 'https://docs.google.com/spreadsheets/d/1hLteGvuivpi-l5mZYowghWjB-vbILK2JnStf0IN6lfc'
url_sorted = "https://docs.google.com/spreadsheets/d/1fZKnEYJ9gxAZBEZCHDeK5UO69AdiRVisd89ltNaNd10"
MIN_MAPPINGS = {\
    'Media & Publicity Team': 'media',
    'AV Team': 'tech',
    'Connect Team (SST .. & more!)': 'connect',
    'Emcee Team': 'emcee',
    'Outreach Team': 'outreach',
    'Assistant Cell Group Leader': 'acgl',
    'Worship Team': 'worship',
    'media': "Media & Publicity Team",
    'tech': 'AV Team',
    'connect': 'Connect Team (SST .. & more!)',
    'emcee': "Emcee Team",
    'outreach': "Outreach Team",
    'acgl': 'Assistant Cell Group Leader',
    'worship': 'Worship Team',
    'Other': 'Other'}


def main():
    gc = gspread.oauth()
    FEB012022 = 1643644800
    errors = 0

    while time.time() < FEB012022:
        now = time.monotonic()
        logging.info("Updating the signup sheeets...")
        try:
            update_ministry_sheets(gc)
        except gspread.exceptions.APIError as e:
            logging.warning(f'Error occured: \n {e}')
            gc = gspread.oauth()
            errors += 1
            if errors < 5:
                continue
            logging.critical("Exceeded the max number of retries. Terminate.")
            return 1
        else:
            timetaken = time.monotonic() - now
            logging.info(f"Done updating signup sheets, time taken = {timetaken}")
            time.sleep(3600)

def update_ministry_sheets(gc):
    form = gc.open_by_url(url).get_worksheet(0)
    sorted_responses = gc.open_by_url(url_sorted)

    # Get all the recruitment data from the form responses sheet
    responses = form.get_all_values()

    # Convert responses into list of youth objects
    all_youths = personify(responses)

    signups_by_ministry = {\
        'media':[],
        'tech': [],
        'connect': [],
        'emcee': [],
        'outreach': [],
        'acgl': [],
        'worship':[],
        'Other': [] }

    # sort the youths into ministry signups
    for youth in all_youths:
        ministryids = [get_minid(ministry) for ministry in youth.ministries]
        for ministry in ministryids:
            signups_by_ministry[ministry].append(youth)

    for k in signups_by_ministry.keys():
        signups_by_ministry[k].sort(key=attrgetter('zone', 'full_name'))

    # Finally, write everything to the file
    worksheets = list(map(lambda x: x.title, sorted_responses.worksheets()))
    for k in signups_by_ministry.keys():
        sheet = None
        logging.info(f"Updating {k}...")
        if MIN_MAPPINGS[k] not in worksheets:
            sorted_responses.add_worksheet(title=MIN_MAPPINGS[k], rows='100', cols='20')
            sheet = sorted_responses.worksheet(MIN_MAPPINGS[k])
            sheet.update('A1:L2', get_header(MIN_MAPPINGS[k]))
        else:
            sheet = sorted_responses.worksheet(MIN_MAPPINGS[k])
        all_data = []
        for i, signup in enumerate(signups_by_ministry[k]):
            all_data.append(get_content(signup, i))
        sheet.update(f'A3:L{len(all_data)+2}', all_data)
        sheet.columns_auto_resize(0, 12)
        logging.info(f"Done Updating {k}")

def get_minid(ministry):
    try:
        minid = MIN_MAPPINGS[ministry]
    except KeyError:
        return 'Other'
    else:
        return minid

def get_content(person, i):
    return [\
        f'{i+1}',
        person.full_name,
        person.contact_hp,
        person.contact_email,
        person.ministry,
        person.cgl,
        person.zone,
        person.experience_bool,
        person.experience_desc,
        person.reason,
        person.questions,
        person.timestamp]


def get_header(title):
    header = [['']*12, [\
        'No.',
        'Full Name',
        'HP Contact',
        'Email',
        'Team',
        'CGL',
        'Age Group / Zone',
        'Has Experience?',
        'Experience Description',
        'Why Serve?',
        'Questions',
        'Timestamp']]
    header[0][0] = title
    return header


def personify(response_list):
    first_row = response_list[0]
    signups = []
    for i in range(1, len(response_list)):
        # Ensure that there are the correct number of fields. 
        # I suspect that if there are no questions it doesn't reflect the response as a ''
        res = response_list[i]
        if len(res) != len(first_row):
            res.append('')
        signups.append(YouthSignup(*res))

    return signups

@dataclass
class YouthSignup:
    timestamp: str
    full_name: str
    contact_hp: str
    contact_email: str
    cgl: str
    zone: str
    ministry: str
    experience_bool: str
    experience_desc: str
    reason: str
    questions: str

    def __post_init__(self):
        self.ministries = self.ministry.split(', ')



if __name__ == '__main__':
    main()
