import wx
import wx.adv
import pandas as pd
from dotenv import load_dotenv
import os
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

load_dotenv()
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME")
MANAGER_PASSWORD = os.getenv("MANAGER_PASSWORD")
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH")
GOOGLE_CHROME_BIN = os.environ.get("GOOGLE_CHROME_BIN")

class HelloFrame(wx.Frame):
    """
    A Frame
    """

    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(HelloFrame, self).__init__(*args, **kw)
        self.SetBackgroundColour('#ffffff')
        self.maxPercent = 100
        self.percent = 0

        self.ok_button = wx.Button(self, wx.ID_OK, label='Ok')
        self.startdatepicker = wx.adv.CalendarCtrl(self, 1, wx.DateTime.Now())
        self.enddatepicker = wx.adv.CalendarCtrl(self, 2, wx.DateTime.Now())
        self.start_date = self.startdatepicker.PyGetDate()
        self.end_date = self.enddatepicker.PyGetDate()
        vertical_container = wx.BoxSizer(wx.VERTICAL)
        vertical_container.AddSpacer(10)
        vertical_container.AddSpacer(10)
        vertical_container.Add(self.startdatepicker, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)
        vertical_container.Add(self.enddatepicker, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)
        vertical_container.AddSpacer(10)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.AddStretchSpacer(1)
        button_sizer.Add(self.ok_button, 0)

        vertical_container.Add(button_sizer, 0, wx.LEFT | wx.RIGHT, 15)
        vertical_container.AddSpacer(20)
        self.SetSizerAndFit(vertical_container)
        self.Bind(wx.adv.EVT_CALENDAR_SEL_CHANGED, self.OnStartDateChanged, self.startdatepicker)
        self.Bind(wx.adv.EVT_CALENDAR_SEL_CHANGED, self.OnEndDateChanged, self.enddatepicker)
        self.Bind(wx.EVT_BUTTON, self.OnOkClick, self.ok_button)
    
    def html_to_dataframe(self, table_header, table_data, course_name=None):
        header_row = []
        df_data = []
        for header in table_header:
            header_row.append(header.text)
        for row in table_data:
            columns = row.find_elements(By.XPATH,"./td") # Use dot in the xpath to find elements with in element.
            table_row = []
            for column in columns:
                table_row.append(column.text)
            df_data.append(table_row)
        df = pd.DataFrame(df_data,columns=header_row)
        df = df.iloc[: , 1:]
        if course_name:
            temp = [course_name for i in range(len(df))]
            df['Course'] = temp
        return df

    def load_options(self):
        # initialize the Chrome driver
        options = Options()
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.binary_location = GOOGLE_CHROME_BIN
        options.add_argument('--headless')
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(chrome_options=options, executable_path=CHROMEDRIVER_PATH)
        # login page
        driver.get("https://trivietedu.ileader.vn/login.aspx")
        # find username/email field and send the username itself to the input field
        driver.find_element("id","user").send_keys(MANAGER_USERNAME)
        # find password input field and insert password as well
        driver.find_element("id","pass").send_keys(MANAGER_PASSWORD)
        # click login button
        driver.find_element(By.XPATH,'//*[@id="login"]/button').click()
        # navigate to lop hoc
        driver.get('https://trivietedu.ileader.vn/Default.aspx?mod=lophoc!lophoc')
        # pulling the main table
        table_header = WebDriverWait(driver, 1.5).until(
                    EC.presence_of_all_elements_located((By.XPATH,'//*[@id="dyntable"]/thead/tr/th')))
        table_data = WebDriverWait(driver, 1.5).until(
                    EC.presence_of_all_elements_located((By.XPATH,'//*[@id="showlist"]/tr')))
        courses_df = self.html_to_dataframe(table_header, table_data)
        # navigate to bai hoc
        driver.get('https://trivietedu.ileader.vn/Default.aspx?mod=lophoc!lophoc_baihoc')
        course_select = Select(WebDriverWait(driver, 1.5).until(
                EC.element_to_be_clickable((By.XPATH,'//*[@id="idlophoc"]'))))
        return driver, courses_df, course_select
    
    def showProgress(self):
        self.progress = wx.ProgressDialog("Pulling Course Data in progress...", "Please wait!", maximum=self.maxPercent, parent=self, style=wx.PD_SMOOTH|wx.PD_AUTO_HIDE)

    def destoryProgress(self):
        self.progress.Destroy()

    def OnStartDateChanged(self, evt):
        self.start_date = evt.PyGetDate()
        self.start_date = datetime.strptime(self.start_date.strftime('%d/%m/%Y'),'%d/%m/%Y').date()
        #print(self.start_date, type(self.start_date))

    def OnEndDateChanged(self, evt):
        self.end_date = evt.PyGetDate()
        self.end_date = datetime.strptime(self.end_date.strftime('%d/%m/%Y'),'%d/%m/%Y').date()
        #print(self.end_date, type(self.end_date))

    def OnOkClick(self, evt):
        driver, courses_df, course_select = self.load_options()
        #start_time = datetime.now()
        commencement = []
        ending = []
        for i in range(len(courses_df)):
            dates = courses_df['Diễn Giải'].to_list()[i].split("\n")[1].split("-")
            dates = [date.strip() for date in dates]
            commencement.append(datetime.strptime(dates[0],'%d/%m/%Y').date())
            ending.append(datetime.strptime(dates[1],'%d/%m/%Y').date())
        courses_df['Commencement Date'] = commencement
        courses_df['Ending Date'] = ending
        cond1 = courses_df[courses_df['Commencement Date'].between(self.start_date, self.end_date)]
        cond2 = courses_df[courses_df['Commencement Date'] <= self.start_date]
        cond2 = cond2[cond2['Ending Date'] >= self.end_date]
        cond3 = courses_df[courses_df['Ending Date'].between(self.start_date, self.end_date)]
        output_df = pd.concat([cond1, cond2, cond3], ignore_index=True, sort=False)
        output_df = output_df.drop_duplicates(subset=['Tên Lớp'])
        final_dates = []
        midterm_dates = []
        percent = 0
        self.maxPercent = len(output_df['Tên Lớp'])
        self.showProgress()
        for course in output_df['Tên Lớp']:
            try:
                course_select.select_by_visible_text(course.split('\n')[0])
                time.sleep(.5)
                # pulling the main table
                table_header = WebDriverWait(driver, 1.5).until(
                            EC.presence_of_all_elements_located((By.XPATH,'//*[@id="dyntable"]/thead/tr/th')))
                table_data = WebDriverWait(driver, 1.5).until(
                            EC.presence_of_all_elements_located((By.XPATH,'//*[@id="showlist"]/tr')))
                time.sleep(.5)
                course_df = self.html_to_dataframe(table_header, table_data)
                temp_midterms = course_df[course_df['Bài học/Lesson'].str.match(r'MIDTERM TEST*') == True]['Ngày'].to_list()
                for midterm in temp_midterms:
                    if "CORRECTION" in course_df.loc[course_df['Ngày']==midterm,('Bài học/Lesson')].to_string():
                        temp_midterms.remove(midterm)
                midterm_dates.append(', '.join(temp_midterms))
                final_dates.append(', '.join(course_df[course_df['Bài học/Lesson'].str.match(r'FINAL TEST*') == True]['Ngày'].to_list()))
                temp_name = output_df[output_df['Tên Lớp']==course]['Tên Lớp'].to_list()[0].split('\n')[0]
                output_df.loc[output_df['Tên Lớp']==course,('Tên Lớp')] = temp_name
                temp_date = output_df.loc[output_df['Tên Lớp']==temp_name,('Diễn Giải')].to_list()[0]
                temp_date = temp_date[temp_date.find("(")+1:temp_date.find(")")]
                output_df.loc[output_df['Tên Lớp']==temp_name,('Diễn Giải')] = temp_date
                percent += 1
                self.progress.Update(percent)
            except:
                percent += 1
                self.progress.Update(percent)
                midterm_dates.append("")
                final_dates.append("")
                pass
        output_df = output_df.rename(columns={"Diễn Giải": "Giờ Học","Thời khóa biểu": "Ngày Học"})
        output_df['Midterm Dates'] = midterm_dates
        output_df['Final Dates'] = final_dates
        output_df['Sĩ số'] = output_df['Sĩ số'].astype('int')
        output_df = output_df[output_df['Sĩ số'] != 0]
        output_df["Commencement Date"] = output_df["Commencement Date"].apply(lambda x: x.strftime('%d/%m/%Y'))
        output_df = output_df[["Tên Lớp","Giờ Học","Ngày Học","Sĩ số","Commencement Date","Midterm Dates","Final Dates"]].sort_values(['Giờ Học'], ascending=True).reset_index(drop=True)
        output_df.index += 1
        # Create a Pandas Excel writer using XlsxWriter as the engine.
        with pd.ExcelWriter(f"Course-List-{self.start_date}-{self.end_date}.xlsx", engine='xlsxwriter') as writer:
            # Write each dataframe to a different worksheet.
            output_df.to_excel(writer, sheet_name='Sheet1')
            # Close the Pandas Excel writer and output the Excel file to the buffer
            writer.save()
        '''
        print(f"Total No of Students: {output_df['Sĩ số'].sum()}")
        end_time = datetime.now()
        print('Duration: {}'.format(end_time - start_time))
        '''

if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frm = HelloFrame(None, title='Course List')
    frm.Show()
    app.MainLoop()