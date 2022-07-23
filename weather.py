#! /usr/bin/env python3

from bs4 import BeautifulSoup as bs
import requests, json, re, sys
from time import strftime
from PyQt6.QtCore import (Qt, QTimer, QTime)
from PyQt6.QtGui import (QImage, QPixmap)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout,
QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton)


class Weather:
    def __init__(self):
        # Get location - lat and long
        location = json.loads(requests.get('http://ipinfo.io/json').text)['loc']
        lat, lon = location.split(',')

        # Get weather page from forecast.weather.gov
        page = requests.get(f'https://forecast.weather.gov/MapClick.php?lat={lat}&lon={lon}')

        # Create the soup
        soup = bs(page.text, 'html.parser')

        # Create some dicts for storing data
        self.data = {}
        summary = {}
        current_conditions = {}

        # Find the header we want and store in the data dict
        self.data['header'] = f"{soup.find('h2', attrs={'class':'panel-title'}).text}"

        # Find current condition summary and data
        weather = soup.find('div', attrs={'id': 'current_conditions-summary'})
        summary['img'] = f"https://forecast.weather.gov/{weather.find('img')['src']}"
        summary['condition'] = weather.find('p', attrs={'class': 'myforecast-current'}).text
        summary['temp f'] = weather.find('p', attrs={'class': 'myforecast-current-lrg'}).text
        summary['temp c'] = weather.find('p', attrs={'class': 'myforecast-current-sm'}).text

        # Find detail data from soup
        table = soup.find('div', attrs={'id': 'current_conditions_detail'})

        # Find the detail header/left td in table and add to dict as keys
        for text in table.findAll('b'):
            current_conditions[text.text] = None

        # Find the data on the right td and add to current_conditions dict
        for key in current_conditions.keys():
            for text in table.findAll('tr'):

                # Using this to get rid of excessive white space in the last dict entry
                if key in text.text.strip():
                    text = re.sub(key, '', text.text.strip())
                    current_conditions[key] = text.replace('\n', '').strip()

        # Add everything to the data dict
        self.data['summary'] = summary
        self.data['details'] = current_conditions


class Window(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedSize(500,270)

        # Iniate the Weather class
        weather = Weather()
        self.summary = weather.data['summary']
        self.details = weather.data['details']

        self.setWindowTitle('PyQt6 Weather App')

        # Create main container
        container = QGridLayout()

        cbox = QHBoxLayout()

        # Create data container
        dgrid = QGridLayout()
        dgrid.setSpacing(1)
        dgrid.setContentsMargins(2, 2, 2, 2)
        dframe = QFrame()
        dframe.setFrameStyle(1)
        dframe.setFrameShadow(QFrame.Shadow.Sunken)
        dframe.setLayout(dgrid)

        # Create the header
        header = QLabel('PyQt6 Weather App')
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet('font-size: 18px; background-color: lightgray; padding: 5 3 5 3; \
        font-weight: bold; border: 1px solid gray; color:steelblue;')

        # Create local header
        self.loc_header = QLabel(f'Current Conditions at {weather.data["header"]}')
        self.loc_header.setStyleSheet('font-size: 12px; color: navy; background-color: lightgray; \
        padding: 5, 3, 5, 3; border: 1px solid gray; font-weight: bold;')

        # Get first init image
        img_url = self.summary['img']
        image = QImage()
        image.loadFromData(requests.get(img_url).content)

        # Create image label
        self.img_label = QLabel()
        self.img_label.setStyleSheet('padding: 3 3 3 3;')
        self.img_label.setPixmap(QPixmap(image))


        # Create detail labels
        i = 0
        self.myvlabels = []
        hlabels = []
        for key, value in self.details.items():
            self.myvlabels.append(value)
            hlabels.append(key)
            hlabels[i] = QLabel(f'<b>{key}</b>:')
            hlabels[i].setStyleSheet('border: 1px solid lightgray; padding: 0 0 0 8;')
            self.myvlabels[i] = QLabel(value)
            self.myvlabels[i].setStyleSheet('border: 1px solid lightgray; padding 0 0 0 0;')
            dgrid.addWidget(hlabels[i], i, 1, 1, 1)
            dgrid.addWidget(self.myvlabels[i], i, 2, 1, 1)
            i += 1

        # Create current conditions label
        text = f'<b>Currently</b>: {self.summary["condition"]} {self.summary["temp f"]} / {self.summary["temp c"]}'
        self.current_label = QLabel(text)
        self.current_label.setFrameStyle(1)
        self.current_label.setFrameShadow(QFrame.Shadow.Sunken)

        # Create a clock
        self.clock = QLabel(f'Current Time: <font color="navy">{strftime("%I:%M:%S %p")}</font>')
        self.clock.setFrameStyle(1)
        self.clock.setFrameShadow(QFrame.Shadow.Sunken)

        # Compact current data and clock
        cbox.addWidget(self.current_label)
        cbox.addWidget(self.clock)

        # Add data widget to data container
        dgrid.addWidget(self.img_label, 0, 0, len(self.details), 1)

        # Add widgets to main container grid
        container.addWidget(header, 0, 0, 1, 1, Qt.AlignmentFlag.AlignTop)
        container.addWidget(self.loc_header, 1, 0, 1, 1, Qt.AlignmentFlag.AlignTop)
        container.addWidget(dframe, 2, 0, 1, 1, Qt.AlignmentFlag.AlignTop)
        container.addLayout(cbox, 3, 0, 1, 1, Qt.AlignmentFlag.AlignTop)

        # Setup the clock timer
        clock_timer = QTimer(self)
        clock_timer.timeout.connect(self.clock_update)
        clock_timer.start(1000)

        # Setup the update timer
        update_timer = QTimer(self)
        update_timer.timeout.connect(self.update)
        update_timer.start(3000000)




        widget = QWidget()
        widget.setLayout(container)
        self.setCentralWidget(widget)

    def clock_update(self):
        self.clock.setText(f'<b>Current Time</b>: <font color="navy">{strftime("%I:%M:%S %p")}</font>')

    def update(self):
        # Iniate the Weather class
        weather = Weather()

        # Set some variables
        summary = weather.data['summary']
        details = weather.data['details']

        # Update the labels
        img_url = self.summary['img']
        image = QImage()
        image.loadFromData(requests.get(img_url).content)
        self.img_label.setPixmap(QPixmap(image))

        i = 0
        for val in details.values():
            self.myvlabels[i].setText(val)
            i += 1

        self.current_label.setText(f'<b>Currently</b>: {summary["condition"]} {summary["temp f"]} / {summary["temp c"]}')

def main():
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
