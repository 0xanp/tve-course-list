import wx
import pandas as pd
from dotenv import load_dotenv
import os
import io
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
from xlsxwriter import Workbook
import gc

class HelloFrame(wx.Frame):
    """
    A Frame that says Hello World
    """

    def __init__(self, *args, **kw):
        # ensure the parent's __init__ is called
        super(HelloFrame, self).__init__(*args, **kw)

        # create a panel in the frame
        pnl = wx.Panel(self)

        # put some text with a larger bold font on it
        st = wx.StaticText(pnl, label="Hello World!")
        font = st.GetFont()
        font.PointSize += 10
        font = font.Bold()
        st.SetFont(font)

        # and create a sizer to manage the layout of child widgets
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(st, wx.SizerFlags().Border(wx.TOP|wx.LEFT, 25))
        pnl.SetSizer(sizer)

        # create a menu bar
        self.makeMenuBar()

        # and a status bar
        self.CreateStatusBar()
        self.SetStatusText("Welcome to wxPython!")


    def makeMenuBar(self):
        """
        A menu bar is composed of menus, which are composed of menu items.
        This method builds a set of menus and binds handlers to be called
        when the menu item is selected.
        """

        # Make a file menu with Hello and Exit items
        fileMenu = wx.Menu()
        # The "\t..." syntax defines an accelerator key that also triggers
        # the same event
        helloItem = fileMenu.Append(-1, "&Hello...\tCtrl-H",
                "Help string shown in status bar for this menu item")
        fileMenu.AppendSeparator()
        # When using a stock ID we don't need to specify the menu item's
        # label
        exitItem = fileMenu.Append(wx.ID_EXIT)

        # Now a help menu for the about item
        helpMenu = wx.Menu()
        aboutItem = helpMenu.Append(wx.ID_ABOUT)

        # Make the menu bar and add the two menus to it. The '&' defines
        # that the next letter is the "mnemonic" for the menu item. On the
        # platforms that support it those letters are underlined and can be
        # triggered from the keyboard.
        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(helpMenu, "&Help")

        # Give the menu bar to the frame
        self.SetMenuBar(menuBar)

        # Finally, associate a handler function with the EVT_MENU event for
        # each of the menu items. That means that when that menu item is
        # activated then the associated handler function will be called.
        self.Bind(wx.EVT_MENU, self.OnHello, helloItem)
        self.Bind(wx.EVT_MENU, self.OnExit,  exitItem)
        self.Bind(wx.EVT_MENU, self.OnAbout, aboutItem)


    def OnExit(self, event):
        """Close the frame, terminating the application."""
        self.Close(True)


    def OnHello(self, event):
        """Say hello to the user."""
        wx.MessageBox("Hello again from wxPython")


    def OnAbout(self, event):
        """Display an About Dialog"""
        wx.MessageBox("This is a wxPython Hello World sample",
                      "About Hello World 2",
                      wx.OK|wx.ICON_INFORMATION)


if __name__ == '__main__':
    # When this module is run (not imported) then create the app, the
    # frame, show it, and start the event loop.
    app = wx.App()
    frm = HelloFrame(None, title='Hello World 2')
    frm.Show()
    app.MainLoop()

# getting credentials from environment variables
load_dotenv()
MANAGER_USERNAME = os.getenv("MANAGER_USERNAME")
MANAGER_PASSWORD = os.getenv("MANAGER_PASSWORD")
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH")
GOOGLE_CHROME_BIN = os.environ.get("GOOGLE_CHROME_BIN")

def html_to_dataframe(table_header, table_data, course_name=None):
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


def load_options():
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
    table_header = WebDriverWait(driver, 3).until(
                EC.presence_of_all_elements_located((By.XPATH,'//*[@id="dyntable"]/thead/tr/th')))
    table_data = WebDriverWait(driver, 3).until(
                EC.presence_of_all_elements_located((By.XPATH,'//*[@id="showlist"]/tr')))
    courses_df = html_to_dataframe(table_header, table_data)
    # navigate to bai hoc
    driver.get('https://trivietedu.ileader.vn/Default.aspx?mod=lophoc!lophoc_baihoc')
    course_select = Select(WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.XPATH,'//*[@id="idlophoc"]'))))
    return driver, courses_df, course_select

driver, courses_df, course_select = load_options()

start_date = st.date_input('Select Start Date', datetime.today())

end_date = st.date_input('Select End Date', datetime.today() + timedelta(days=7))

all_courses = st.button('Show All Course')


if all_courses:
    start_time = datetime.now()
    commencement = []
    ending = []
    for i in range(len(courses_df)):
        dates = courses_df['Diễn Giải'].to_list()[i].split("\n")[1].split("-")
        dates = [date.strip() for date in dates]
        commencement.append(datetime.strptime(dates[0],'%d/%m/%Y').date())
        ending.append(datetime.strptime(dates[1],'%d/%m/%Y').date())
    courses_df['Commencement Date'] = commencement
    courses_df['Ending Date'] = ending
    cond1 = courses_df[courses_df['Commencement Date'].between(start_date, end_date)]
    cond2 = courses_df[courses_df['Commencement Date'] <= start_date]
    cond2 = cond2[cond2['Ending Date'] >= end_date]
    cond3 = courses_df[courses_df['Ending Date'].between(start_date, end_date)]
    output_df = pd.concat([cond1, cond2, cond3], ignore_index=True, sort=False)
    del [[dates, ending, commencement, cond1, cond2, cond3]]
    final_dates = []
    midterm_dates = []
    for course in output_df['Tên Lớp']:
        course_select.select_by_visible_text(course.split('\n')[0])
        time.sleep(.5)
        # pulling the main table
        table_header = WebDriverWait(driver, 2).until(
                    EC.presence_of_all_elements_located((By.XPATH,'//*[@id="dyntable"]/thead/tr/th')))
        table_data = WebDriverWait(driver, 2).until(
                    EC.presence_of_all_elements_located((By.XPATH,'//*[@id="showlist"]/tr')))
        time.sleep(.5)
        course_df = html_to_dataframe(table_header, table_data)
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
        st.success(course.split('\n')[0],icon="✅")
        del [[temp_midterms, course_df, temp_name, temp_date, table_header, table_data]]
        gc.collect()
    output_df = output_df.rename(columns={"Diễn Giải": "Giờ Học","Thời khóa biểu": "Ngày Học"})
    output_df['Midterm Dates'] = midterm_dates
    output_df['Final Dates'] = final_dates
    output_df['Sĩ số'] = output_df['Sĩ số'].astype('int')
    output_df = output_df[["Tên Lớp","Giờ Học","Ngày Học","Sĩ số","Commencement Date","Midterm Dates","Final Dates"]].sort_values(['Giờ Học'], ascending=True).reset_index(drop=True)
    st.table(output_df)
    buffer = io.BytesIO()
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Write each dataframe to a different worksheet.
        output_df.to_excel(writer, sheet_name='Sheet1')
        # Close the Pandas Excel writer and output the Excel file to the buffer
        writer.save()
        st.download_button(
            label="Download Excel worksheets",
            data=buffer,
            file_name=f'{start_date}-to-{end_date}.xlsx',
            mime="application/vnd.ms-excel"
        )
    st.write(f"Total No of Students: {output_df['Sĩ số'].sum()}")
    end_time = datetime.now()
    st.write('Duration: {}'.format(end_time - start_time))
    del [[output_df, buffer, final_dates, midterm_dates]]
    gc.collect()
