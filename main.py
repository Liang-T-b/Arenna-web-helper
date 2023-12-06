# <<<<<<< Updated upstream
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import json
import os

EVAL_NUM = 2
INIT_ELO=1600#baseline_4水平
class pa_chong():
    def __init__(self):
        #如果last_name和 last_NAME_counts顺序与平台里的先后顺序不一致，可能存在问题。
        self.model_list = []
        self.train_task = {}
        self.eval_task_list = []
        self.time = 600
        self.better_modle = []
        self.eval_result_dict = {}
        self.elo_dic={}
        self.model_task = {}
        if os.path.exists('elo.json'):
            f2 = open('elo.json', 'r')
            self.elo_dic = json.load(f2)
            print("load elo file")
        if os.path.exists('task.json'):
            with open('task.json','r') as f3:
                data = json.load(f3)
                self.train_task = data[0]
                self.enemy_pool = data[1]
                print("load task file")

        with open('modle.json', 'r') as f:
            self.model_list = json.load(f)
            print("load modle file")

        with open('task1.json', 'r') as f:
            self.eval_task_list = json.load(f)
            print("load task1 file")
        
        with open('modle_1.json', 'r') as f:
            self.better_modle = json.load(f)
            print("load model1 file")
    
    def go(self):
        # 初始化浏览器
        self.browser = webdriver.Edge()
        #PART1:自动化登陆 打开登录页面
        login_url = 'https://aiarena.tencent.com/p/user/login?redirect=https%3A%2F%2Faiarena.tencent.com%2Flogin'
        self.browser.get(login_url)
        # 输入用户名和密码
        username = self.browser.find_element(By.ID,'basic_email')  # 替换为实际的用户名输入框定位方法
        password = self.browser.find_element(By.ID, 'basic_password') # 替换为实际的密码输入框定位方法
        submit = self.browser.find_element(By.XPATH,'//*[@id="basic"]/div[4]/div/div/div/span/button')
        username.send_keys('1374203630@qq.com')
        password.send_keys('chenbo060010')
        submit.click()
        time.sleep(5)
        while True:
            # self.download_modle()
            # self.model_list = self.eval_model(self.model_list, self.enemy_pool[0],1)
            # self.load_modle()
            self.eval_result()
            self.load_task()
            self.get_elo_score()
            self.save_result()
            # self.handle_result()
            # self.better_modle = self.eval_model(self.better_modle, self.enemy_pool[1],2)
            
            # self.load_modle_1()
            # time.sleep(self.time)

    def build_modle_name(self, task_name, train_total_time, train_time):
        task = task_name.split("-")
        name1 = str(task[0]) if len(task) == 1 else str(task[0] +"-"+ task[1])
        total_time = train_total_time.split("-")
        time1 = total_time[2].split("h")[0]
        try:
            time1_hour = int(time1)
        except:time1_hour = 0
        time2 = train_time.split("m")[0]
        time2_s_h = time2.split("h")
        time2_hour = int(time2_s_h[0] if len(time2_s_h) > 1 else '0') 
        time2_min = time2.split("h")[1] if  len(time2_s_h) > 1 else time2.split("h")[0]
        name2 = str(str(time1_hour + time2_hour) +'h'+ time2_min)
        return name1 +'-'+ name2

    def download_modle(self):
        last_train_time = str()
        task_list = dict(self.train_task)
        for (task_name, train_time) in task_list.items():
            self.browser.get('https://aiarena.tencent.com/p/competition-exp/21/cluster-training')
            time.sleep(5)
            while(True):
                    try:
                        s = self.browser.find_element(By.XPATH, '//*[@id="name"]')
                        break
                    except:
                        time.sleep(1)
            s.send_keys(task_name)
            time.sleep(3)
            self.browser.find_element(By.XPATH, 
                                        '//*[@id="root"]/div/div/section/section/main/div/div/div[2]/div/div/div/div/form/div/div[1]/div[2]/div/div/div/span/span/span[2]/button').click()
            time.sleep(2)
            td_list = self.browser.find_element(By.XPATH,
                                        '//*[@id="root"]/div/div/section/section/main/div/div/div[2]/div/div/div/div/div[2]/div/div/div/div/div/table').find_elements(By.TAG_NAME, 'tr')[2].find_elements(By.TAG_NAME, 'td')
            if td_list[1].text != task_name:continue
            train_total_time =  td_list[6].text
            self.browser.find_element(By.XPATH, 
                f'//*[@id="root"]/div/div/section/section/main/div/div/div[2]/div/div/div/div/div[2]/div/div/div/div/div/table/tbody/tr[2]/td[12]/div/div/div[2]/button').click()
            
            while(True):
                try:
                    self.browser.find_element(By.XPATH, 
                                                '/html/body/div[2]/div/div[2]/div/div/div[2]/div/div/div/div/div/div/div/div/div/div/table/tbody/tr[2]/td[3]/div/div/div[2]/span/button')
                    break
                except:
                    time.sleep(1)
            tr1_list = self.browser.find_element(By.XPATH, 
                                            '/html/body/div[2]/div/div[2]/div/div/div[2]/div/div/div/div/div/div/div/div/div/div/table/tbody').find_elements(By.TAG_NAME, 'tr')
            train_time_now  = tr1_list[1].find_elements(By.TAG_NAME, 'td')[0].text
            last_train_time = tr1_list[1].find_elements(By.TAG_NAME, 'td')[0].text
            if train_time_now == train_time:break
            self.browser.find_element(By.XPATH, 
                '/html/body/div[2]/div/div[2]/div/div/div[2]/div/div/div/div/div/div/div/div/div/div/table/tbody/tr[2]/td[3]/div/div/div[2]/span/button').click()
            time.sleep(3)
            input1_s2 = self.browser.find_element(By.XPATH, 
                                                    '/html/body/div[3]/div/div[2]/div/div/div[2]/form/div/div[1]/div[1]/div[2]/div[1]/div/span/input')
            model_name = self.build_modle_name(task_name, train_total_time, train_time_now)
            input1_s2.send_keys(model_name)
            input2_s2 = self.browser.find_element(By.XPATH, '/html/body/div[3]/div/div[2]/div/div/div[2]/form/div/div[1]/div[4]/div[2]/div/div/div/textarea')
            input2_s2.send_keys(task_name +'_'+ train_time)
            time.sleep(2)
            self.browser.find_element(By.XPATH, '/html/body/div[3]/div/div[2]/div/div/div[2]/form/div/div[2]/div/div[1]/span/button').click()
            time.sleep(3)
            self.model_list.append(model_name)
            self.model_task[model_name] = task_name
            self.browser.get('https://aiarena.tencent.com/p/competition-exp/21/cluster-training')
            time.sleep(3)
            self.train_task[task_name] = last_train_time
            
    
    def eval_model(self, model_list, enemy,num):
        if len(model_list) == 0 or len(self.eval_task_list) >= 10:return model_list 
        model_to_eval = list(model_list)
        for model_name in model_to_eval:
            self.browser.get('https://aiarena.tencent.com/p/competition-exp/21/model-manage')
            while(True):
                try:
                    s = self.browser.find_element(By.XPATH, '//*[@id="name"]')
                    break
                except:
                    time.sleep(1)
            s.send_keys(model_name)
            time.sleep(3)
            self.browser.find_element(By.XPATH, 
                                    '//*[@id="root"]/div/div/section/section/main/div/div/div[2]/div/div/div/div/form/div/div[1]/div[2]/div/div/div/span/span/span[2]/button').click()
            time.sleep(2)
            td_list = self.browser.find_element(By.XPATH,
                                    '/html/body/div/div/div/section/section/main/div/div/div[2]/div/div/div/div/div/div/div/div/div/div/table').find_elements(By.TAG_NAME, 'tr')[2].find_elements(By.TAG_NAME, 'td')
            if td_list[3].text == '检测中' or td_list[3].text == '待检测':break
            elif td_list[3].text == '检测失败':
                model_list.remove(model_name)
                break
            self.browser.find_element(By.XPATH, 
                                    '//*[@id="root"]/div/div/section/section/main/div/div/div[2]/div/div/div/div/div/div/div/div/div/div/table/tbody/tr[2]/td[12]/div/div/div[1]/span/button').click()
            while(True):
                try:
                    self.browser.find_element(By.XPATH,'/html/body/div[2]/div/div[2]/div/div/div[2]/form/div/div[2]/div/div[1]/span/button')
                    break
                except:
                    time.sleep(1)
            self.browser.find_element(By.XPATH,
                                    '/html/body/div[2]/div/div[2]/div/div/div[2]/form/div/div[1]/div[5]/div[2]/div[1]/div/span/input').send_keys(model_name + '_'+str(num))
            eval_select1_option = self.browser.find_element(By.XPATH,'/html/body/div[2]/div/div[2]/div/div/div[2]/form/div/div[1]/div[7]/div[2]/div/div/div/div[2]/div[2]/div[1]/div/span/div/div/div[1]/div/div/input')
            eval_select1_option.click()
            for _ in range(3):
                eval_select1_option.send_keys(Keys.ARROW_DOWN)
                    # 使用回车键选择选项
                eval_select1_option.send_keys(Keys.ENTER)
            eval_select2_element = self.browser.find_element(By.XPATH,'/html/body/div[2]/div/div[2]/div/div/div[2]/form/div/div[1]/div[8]/div[2]/div/div/div/div[1]/div[2]/div/div/span/div/div/span[1]/input')
            eval_select2_element.click()
            time.sleep(3)
            eval_select2_element.send_keys(Keys.TAB)
            time.sleep(3)
            activate_element = self.browser.switch_to.active_element
            activate_element.send_keys(enemy)
            time.sleep(3)
            eval_select2_element.send_keys(Keys.ARROW_DOWN)
                # 使用回车键选择选项
            eval_select2_element.send_keys(Keys.ENTER)
            eval_select3_element=self.browser.find_element(By.XPATH,'/html/body/div[2]/div/div[2]/div/div/div[2]/form/div/div[1]/div[8]/div[2]/div/div/div/div[2]/div[2]/div/div/span/div/div/div[1]/div/div/input')
            eval_select3_element.click()
            for _ in range(3):
                eval_select3_element.send_keys(Keys.ARROW_DOWN)
                # 使用回车键选择选项
                eval_select3_element.send_keys(Keys.ENTER)
            s3=self.browser.find_element(By.XPATH,'/html/body/div[2]/div/div[2]/div/div/div[2]/form/div/div[1]/div[9]/div[2]/div/div/div/div[1]/div[2]/div/div/div/div/div[2]/input')
            #删除现有轮数
            s3.send_keys(Keys.CONTROL+'a')
            s3.send_keys(Keys.DELETE)
            s3.send_keys(EVAL_NUM)
            time.sleep(1)
            self.browser.find_element(By.XPATH,
                                    '//*[@id="desc"]').send_keys(self.model_task[model_name])
            time.sleep(1)
            self.browser.find_element(By.XPATH,'/html/body/div[2]/div/div[2]/div/div/div[2]/form/div/div[2]/div/div[1]/span/button').click()
            time.sleep(1)
            self.eval_task_list.append(model_name + '_' +str(num))
            model_list.remove(model_name)
            if len(self.eval_task_list) >= 10:return model_list
        return model_list

    def eval_result(self):
        if len(self.eval_task_list) == 0:return
        task_list = list(self.eval_task_list)
        for task in task_list:
            self.browser.get('https://aiarena.tencent.com/p/competition-exp/21/model-access')
            while(True):
                    try:
                        s = self.browser.find_element(By.XPATH, '//*[@id="name"]')
                        break
                    except:
                        time.sleep(1)
            s.send_keys(task)
            time.sleep(3)
            self.browser.find_element(By.XPATH, '//*[@id="root"]/div/div/section/section/main/div/div/div[2]/div/div/div/form/div/div[1]/div[2]/div/div/div/span/span/span[2]/button').click()
            time.sleep(5)
            table = self.browser.find_element(By.XPATH,
                                            '//*[@id="root"]/div/div/section/section/main/div/div/div[2]/div/div/div/div/div/div/div/div/div/table/tbody')
            tr_list = table.find_elements(By.TAG_NAME, 'tr')
            td_list = tr_list[1].find_elements(By.TAG_NAME, 'td')
            if td_list[1].text == '已完成' or td_list[1].text == '已失败':
                self.eval_result_dict[td_list[3].text+"_vs_" + td_list[5].text]=td_list[2].text
                time.sleep(1)
                self.eval_task_list.remove(task)

    def get_elo_score(self):
        K = 32
        def expected_result(player1_elo, player2_elo):
            return 1 / (1 + 10**((player2_elo - player1_elo) / 400))
        for key,value in list(self.eval_result_dict.items()):
            model=key.split("_vs_")
            model_a=model[0]
            model_b=model[1]
            if model_a not in self.elo_dic:
                self.elo_dic[model_a]=INIT_ELO
            if model_b not in self.elo_dic:
                self.elo_dic[model_b]=INIT_ELO
            numbers=re.findall(r'\d+',value)
            numbers=[int(number) for number in numbers]
            W_a = numbers[0] / numbers[2]
            W_b = numbers[1] / numbers[2]
            # if W_b<0.5 and model_b==self.enemy_pool[-1]:
            #     print(self.enemy_pool)
            #     self.updata_enemy_pool()
            #     print(self.enemy_pool)
            # print(model_a,model_b,numbers)
            E_a = expected_result(self.elo_dic[model_a],self.elo_dic[model_b])
            E_b = expected_result(self.elo_dic[model_b],self.elo_dic[model_a])
            self.elo_dic[model_a] = self.elo_dic[model_a] + K * (W_a - E_a)
            #暂时不更新baseline的分数
            self.elo_dic[model_b] = self.elo_dic[model_b] + K * (W_b - E_b)
            self.eval_result_dict.pop(key)
        # print(self.elo_dic)

    def save_result(self):
        elo_json = json.dumps(self.elo_dic,sort_keys=False, indent=4, separators=(',', ': '))
        f = open('elo.json', 'w')
        f.write(elo_json)
        task_to_write=[self.train_task,self.enemy_pool]
        with open('task.json','w') as json_file:
            json.dump(task_to_write, json_file)

    def updata_enemy_pool(self):
        #取出最新的对手
        last_enemy_name=self.enemy_pool[-1]
        cnt=last_enemy_name.split("-")
        new_cnt=int(cnt[1])+1
        self.enemy_pool.pop(0)
        self.enemy_pool.append("baseline-"+str(new_cnt))
        
    def load_modle(self):
        # 将列表保存至JSON文件
        with open('modle.json', 'w') as f:
            json.dump(self.model_list, f)
    
    def load_task(self):
        # 将列表保存至JSON文件
        with open('task1.json', 'w') as f:
            json.dump(self.eval_task_list, f)
    
    def load_modle_1(self):
        # 将列表保存至JSON文件
        with open('modle_1.json', 'w') as f:
            json.dump(self.better_modle, f)


    def handle_result(self):
        eval_result_dict = dict(self.eval_result_dict)
        for (modle_name,result) in eval_result_dict.items():
            win = int(result.split("/")[0])
            lose = int((result.split("/")[1]).split("(")[0])
            if win/lose >= 1.0:
                self.better_modle.append(modle_name.split("_")[0])
                self.eval_result_dict.pop(modle_name)



if __name__ == "__main__":
    m = pa_chong()
    m.go()