import json
import pandas as pd

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

class ChatConsumer(WebsocketConsumer):

    # 사용자와 websocket 연결이 맺어졌을 때 호출
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_%s" % self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    # 사용자와 websocket 연결이 끊겼을 때 호출
    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )
    

    # 전역변수 선언
    global idx, pass_cnt, step_pass, q_pass, whotmp, wheretmp, whentmp

    idx = 0 # 초기에 0, 누구 = 1, 어디에서 = 2, 언제 = 3, 재확인 = 4
    pass_cnt = 0 # 아니오를 2번 이상 답할 경우 대상을 모르는 것으로 알고 다음 질문을 넘어감
                 # 예를 들어 누가 때렸는지 알아요? 라는 질문에 2번 아니오라 답하면 때린 인물이 기억이 안나는 것으로 보고 '어디서' 질문으로 넘어감
    step_pass = False
                 # 다음 label 질문으로 넘어가도 되는지 확인하는 bool
    q_pass = False
    whotmp = ""
    wheretmp = ""
    whentmp = ""

    # Receive message from WebSocket
    # 사용자가 메시지를 보내면 호출
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        global idx, pass_cnt, step_pass, q_pass, whotmp, wheretmp, whentmp

        temp_who_0 = who_df.query('label == [0]').sample(n=5) # csv에서 랜덤으로 라벨이 0인 질문 5개 추출
        temp_who_0 = temp_who_0.loc[:, 'Q'].tolist() # 뽑은 질문을 리스트로 변환
        temp_who_1 = who_df.query('label == [1]').sample(n=5) # 라벨이 1인 질문 중 5개를 랜덤으로 추출
        temp_who_1 = temp_who_1.loc[:, 'Q'].tolist()

        temp_where_0 = place_df.query('label == [0]').sample(n=5)
        temp_where_0 = temp_where_0.loc[:, 'Q'].tolist()
        temp_where_1 = place_df.query('label == [1]').sample(n=5)
        temp_where_1 = temp_where_1.loc[:, 'Q'].tolist()

        temp_when_0 = when_df.query('label == [0]').sample(n=5)
        temp_when_0 = temp_when_0.loc[:, 'Q'].tolist()
        temp_when_1 = when_df.query('label == [1]').sample(n=5)
        temp_when_1 = temp_when_1.loc[:, 'Q'].tolist()

        no_ans_who = '모르는 사람'
        no_ans_where = '모르는 장소'
        no_ans_when = '모르는 시간'
        
        if(idx == 0):
            message += '<br><br>' + temp_who_0[0]
            idx += 1

        elif(idx == 1):

            if(step_pass == False):
                if(message == '네'):
                    q_pass = True
                    step_pass = True
                    message += '<br><br>' + temp_who_1[0]
                elif(message == '아니오'):
                    pass_cnt += 1
                    if(pass_cnt == 2):
                        message += '<br><br>기억이 나지 않나 보네요.\n괜찮습니다. 나중에라도 기억이 나면 알려주세요.'
                        whotmp = no_ans_who
                        message += '<br><br>' + temp_where_0[0].replace('{tag_people}', whotmp)
                        step_pass = False
                        pass_cnt = 0
                        idx += 1
                    else:    
                        message += '<br><br>장애인 분을 위해서 때린 사람이 누구인지 확실하게 알 필요가 있어요.\
                            <br>질문이 이해가 안 가시면 잘 모르겠다고 답해주세요.\
                            <br>기억이 나지 않는다면 한 번 더 아니오를 눌러주세요.\
                            <br>아니오를 한 번 더 누르면 다음 질문을 할게요.'
                        message += '<br><br>질문을 다르게 해볼게요.'
                        message += '<br><br>' + temp_who_0[0]
                    
                elif('잘 모르겠' in message):
                    message += '<br><br>질문을 다르게 해볼게요.'
                    message += '<br><br>' + temp_who_0[0]
                    q_pass = True

            elif(step_pass == True):
                if('잘 모르겠' in message):
                    message += '<br><br>질문을 다르게 해볼게요.'
                    message += '<br><br>' + temp_who_1[0]
                else:
                    ans_pass = __anschk__(message, entity_who)
                    if ans_pass:
                        whotmp = message
                        message += '<br><br>때린 사람이 '+whotmp+'(이)였군요.\n이제부터 '+whotmp+'(이)가 어디서 때렸는지 물어볼게요'
                        message += '<br><br>' + temp_where_0[0].replace('{tag_people}', whotmp)
                        idx += 1
                        step_pass = False

                    elif not ans_pass:
                        message += "<br><br>'인물' 항목에서 답변해주세요."
                        message += '<br><br>질문을 다시 할게요.'
                        message += '<br><br>' + temp_who_1[0]
                    
        elif(idx == 2):
            
            if(step_pass == False):
                if(message == '네'):
                    q_pass = True
                    step_pass = True
                    message += '<br><br>' + temp_where_1[0].replace('{tag_people}', whotmp)
                elif(message == '아니오'):
                    pass_cnt += 1
                    if(pass_cnt == 2):
                        message += '<br><br>기억이 나지 않나 보네요.\n괜찮습니다. 나중에라도 기억이 나면 알려주세요.'
                        wheretmp = no_ans_where
                        message += '<br><br>' + temp_when_0[0].replace('{tag_people}', whotmp).replace('{tag_place}', wheretmp)
                        step_pass = False
                        pass_cnt = 0
                        idx += 1
                    else:    
                        message += '<br><br>장애인 분을 위해서 '+whotmp+'(이)가 어디서 때렸는지 확실하게 알 필요가 있어요.\
                            <br>질문이 이해가 안 가시면 잘 모르겠다고 답해주세요.\
                            <br>기억이 나지 않는다면 한 번 더 아니오를 눌러주세요.\
                            <br>아니오를 한 번 더 누르면 다음 질문을 할게요.'
                        message += '<br><br>질문을 다르게 해볼게요.'
                        message += '<br><br>' + temp_where_0[0].replace('{tag_people}', whotmp)

                elif('잘 모르겠' in message):
                    message += '<br><br>질문을 다르게 해볼게요.'
                    message += '<br><br>' + temp_where_0[0].replace('{tag_people}', whotmp)
                    q_pass = True

            elif(step_pass == True):
                if('잘 모르겠' in message):
                    message += '<br><br>질문을 다르게 해볼게요.'
                    message += '<br><br>' + temp_where_1[0].replace('{tag_people}', whotmp)
                else:
                    ans_pass = __anschk__(message, entity_place)
                    if ans_pass:
                        wheretmp = message
                        message += '<br><br>' + whotmp+'(이)가 때린 장소가 '+wheretmp+'(이)였군요.\n이제부터 '+whotmp+'(이)가 언제 때렸는지 물어볼게요'
                        message += '<br><br>' + temp_when_0[0].replace('{tag_people}', whotmp).replace('{tag_place}', wheretmp)
                        idx += 1
                        step_pass = False
                    elif not ans_pass:
                        message += "<br><br>'장소' 항목에서 답변해주세요."
                        message += '<br><br>질문을 다시 할게요.'
                        message += '<br><br>' + temp_where_1[0].replace('{tag_people}', whotmp)
                    

        elif(idx == 3):

            if(step_pass == False):
                if(message == '네'):
                    q_pass = True
                    step_pass = True
                    message += '<br><br>' + temp_when_1[0].replace('{tag_people}', whotmp).replace('{tag_place}', wheretmp)
                elif(message == '아니오'):
                    pass_cnt += 1
                    if(pass_cnt == 2):
                        message += '<br><br>기억이 나지 않나 보네요.\n괜찮습니다. 나중에라도 기억이 나면 알려주세요.'
                        whentmp = no_ans_when
                        message += '<br><br>다시 한번 확인할게요. ' +whotmp + '(이)가 '+wheretmp+'에서 '+whentmp+'에, 당신을 때린게 맞나요?'
                        step_pass = False
                        pass_cnt = 0
                        idx += 1
                    else:    
                        message += '<br><br>장애인 분을 위해서 '+whotmp+'(이)가 언제 때렸는지 확실하게 알 필요가 있어요.\
                            <br>질문이 이해가 안 가시면 잘 모르겠다고 답해주세요.\
                            <br>기억이 나지 않는다면 한 번 더 아니오를 눌러주세요.\
                            <br>아니오를 한 번 더 누르면 다음 질문을 할게요.'
                        message += '<br><br>질문을 다르게 해볼게요.'
                        message += '<br><br>' + temp_when_0[0].replace('{tag_people}', whotmp).replace('{tag_place}', wheretmp)

                elif '잘 모르겠' in message:
                    message += '<br><br>질문을 다르게 해볼게요.'
                    message += '<br><br>' + temp_where_0[0].replace('{tag_people}', whotmp).replace('{tag_place}', wheretmp)
                    q_pass = True
            
            elif(step_pass == True):
                if('잘 모르겠' in message):
                    message += '<br><br>질문을 다르게 해볼게요.'
                    message += '<br><br>' + temp_when_1[0].replace('{tag_people}', whotmp).replace('{tag_place}', wheretmp)
                else:
                    ans_pass = __anschk__(message, entity_time)
                    if ans_pass:
                        whentmp = message
                        message += '<br><br>' + whotmp+'(이)가 '+wheretmp+'에서 장애인님을 때렸군요. 때린 시간은 '+whentmp+'(이)였구요'
                        message += '<br><br>다시 한번 확인할게요. ' +whotmp + '(이)가 '+wheretmp+'에서 '+whentmp+'에, 당신을 때린게 맞나요?'
                        idx += 1
                        step_pass = False
                    elif not ans_pass:
                        message += "<br><br>'시간' 항목에서 답변해주세요."
                        message += '<br><br>질문을 다시 할게요.'
                        message += '<br><br>' + temp_when_1[0].replace('{tag_people}', whotmp).replace('{tag_place}', wheretmp)
                    

        elif(idx == 4):

            if(message == '네'):
                message += '<br><br>신고가 정상적으로 접수되었습니다. 금방 연락을 드릴게요.'
                idx = 0
            elif(message == '아니오'):
                message += '<br><br>어디가 틀린건지 얘기해주세요.'
            else:
                if(message == '누가'):
                    idx = 1
                    message += '<br><br>' + temp_who_0[0]
                elif(message == '어디서'):
                    idx = 2
                    message += '<br><br>' + temp_where_0[0].replace('{tag_people}', whotmp)
                elif(message == '언제'):
                    idx = 3
                    message += '<br><br>' + temp_where_0[0].replace('{tag_people}', whotmp).replace('{tag_place}', wheretmp)


        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {
                "type": "chat_message",
                "message": message,
            }
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            "message": message,
        }))

# 질문 db 불러오기
who_df = pd.read_csv("./dataset/query_who.csv", encoding='cp949')
place_df = pd.read_csv("./dataset/query_place.csv") 
when_df = pd.read_csv("./dataset/query_when.csv") 
what_df = pd.read_csv("./dataset/query_what.csv") 
where_df = pd.read_csv("./dataset/query_where.csv") 
entity_df = pd.read_csv("./dataset/entity_dataset.csv", encoding='cp949')

# entity 항목 불러오기
entity_who = entity_df.loc[0, 'entity'].split(', ')
entity_place = entity_df.loc[1, 'entity'].split(', ')
entity_time = entity_df.loc[2, 'entity'].split(', ')
entity_object = entity_df.loc[3, 'entity'].split(', ')
entity_body = entity_df.loc[4, 'entity'].split(', ')

# 언제에 해당하는 entity에 시간 추가
for i in range(1, 13):
    tmp = str(i) + '시'
    entity_time.append(tmp)

# 장애인이 틀렸다고 한 부분만 다시 입력하는 기능
# 입력한 내용인 db에 있는지 확인
# ex) 장애인이 때린 사람을 아저씨, 활동보조인으로 입력
# db에 '아저씨', '활동보조인'이 없을 경우 재입력 요구
def __anschk__(ans, df):

    if ans in df:
        return True

    return False

expected_A1 = {'네', '아니요', '잘 모르겠어요'}

## 함수 호출 X ##
# 누가
def __who__(message):
    
    no_ans = '모르는 사람' 
    temp = who_df.query('label == [0]').sample(n=5) # csv에서 랜덤으로 라벨이 0인 질문 5개 추출
    temp = temp.loc[:, 'Q'].tolist() # 뽑은 질문을 리스트로 변환
    pass_cnt = 0 # 아니오를 2번 이상 답할 경우 대상을 모르는 것으로 알고 다음 질문을 넘어감
                 # 예를 들어 누가 때렸는지 알아요? 라는 질문에 2번 아니오라 답하면 때린 인물이 기억이 안나는 것으로 보고 '어디서' 질문으로 넘어감
    step_pass = False
                 # 다음 label 질문으로 넘어가도 되는지 확인하는 bool

    for q in temp:
        if step_pass:
            break
        # message += '<br><br>' + q
        print(q)
        q_pass = False
        # label은 그대로하고 질문만 새롭게 출력하는 것을 확인하는 bool
        while not q_pass:
            ans = message
            if ans == '네':
                q_pass = True
                step_pass = True
                message += '\n\n' + ans
            elif ans == '아니요':
                message += '<br><br>' + ans
                pass_cnt += 1
                if pass_cnt == 2:
                    return no_ans
                elif q == temp[-1]:
                    message += '<br><br>기억이 나지 않나 보네요.\n괜찮습니다. 나중에라도 기억이 나면 알려주세요.'  
                    return no_ans                 
                message += ('<br><br>장애인 분을 위해서 때린 사람이 누구인지 확실하게 알 필요가 있어요.\
                    \n질문이 이해가 안 가시면 잘 모르겠다고 답해주세요/\
                    \n기억이 나지 않는다면 한 번 더 아니오를 눌러주세요.\
                    \n아니오를 한 번 더 누르면 다음 질문을 할게요.')
                message += ('<br><br>질문을 다르게 해볼게요.')
                q_pass = True
            elif '잘 모르겠' in ans:
                message += ('<br><br>잘 모르겠어요')
                message += ('<br><br>질문을 다르게 해볼게요.')
                q_pass = True

        if q == temp[-1] and step_pass == False:
            message += ('<br><br>기억이 나지 않나 보네요.\n괜찮습니다. 나중에라도 기억이 나면 알려주세요.')
            return no_ans

    temp = who_df.query('label == [1]').sample(n=5) # 라벨이 1인 질문 중 5개를 랜덤으로 추출
    temp = temp.loc[:, 'Q'].tolist()
    step_pass = False

    for q in temp:
        if step_pass:
            break
        print(q)
        q_pass = False
        while not q_pass:
            ans = message

            if '잘 모르겠' in ans:
                print('잘 모르겠어요')
                print('질문을 다르게 해볼게요.')
                q_pass = True
                
            else:
                print(ans)
                ans_pass = __anschk__(ans, entity_who)
                if ans_pass:
                    whotmp = ans
                elif not ans_pass:
                    print("'인물' 항목에서 답변해주세요.")
                    print('질문을 다시 할게요.')
                    q_pass = True
                    continue
                print('때린 사람이 '+whotmp+'(이)였군요.\n이제부터 '+whotmp+'(이)가 어디서 때렸는지 물어볼게요')
                q_pass = True
                step_pass = True
                

    return whotmp

# 어디서
def __place__(who, screen):

    no_ans = '모르는 장소'
    temp = place_df.query('label == [0]').sample(n=5)
    temp = temp.loc[:, 'Q'].tolist()
    step_pass = False
    pass_cnt = 0
    
    for q in temp:
        if step_pass:
            break
        q = q.replace('{tag_people}', who)
        print(q)
        q_pass = False
        while not q_pass:
            ans = YNanswer(screen)
            if ans == '네':
                q_pass = True
                step_pass = True
                print(ans)
            elif ans == '아니요':
                print(ans)
                pass_cnt += 1
                if pass_cnt == 2:
                    return no_ans
                elif q == temp[-1]:
                    print('기억이 나지 않나 보네요.\n괜찮습니다. 나중에라도 기억이 나면 알려주세요.')   
                    return no_ans                    
                print('장애인 분을 위해서 '+who+'(이)가 어디서 때렸는지 확실하게 알 필요가 있어요.\
                    \n질문이 이해가 안 가시면 잘 모르겠다고 답해주세요/\
                    \n기억이 나지 않는다면 한 번 더 아니오를 눌러주세요.\
                    \n아니오를 한 번 더 누르면 다음 질문을 할게요.')
                print('질문을 다르게 해볼게요.')
                q_pass = True
            elif '잘 모르겠' in ans:
                print('잘 모르겠어요')
                print('질문을 다르게 해볼게요.')
                q_pass = True

        if q == temp[-1] and step_pass == False:
            print('기억이 나지 않나 보네요.\n괜찮습니다. 나중에라도 기억이 나면 알려주세요.')
            return no_ans

    temp = place_df.query('label == [1]').sample(n=5)
    temp = temp.loc[:, 'Q'].tolist()
    step_pass = False

    for q in temp:
        if step_pass:
            break
        q_pass = False
        q = q.replace('{tag_people}', who)
        print(q)
        step_pass = False
        while not q_pass:
            ans = SPanswer(screen)

            if '잘 모르겠' in ans:
                print('잘 모르겠어요')
                print('질문을 다르게 해볼게요.')
                q_pass = True
                
            else:
                print(ans)
                ans_pass = __anschk__(ans, entity_place)
                if ans_pass:
                    whentmp = ans
                elif not ans_pass:
                    print("'장소' 항목에서 답변해주세요.")
                    print('질문을 다시 할게요.')
                    continue
                print(who+'(이)가 때린 장소가 '+whentmp+'(이)였군요.\n이제부터'+who+'(이)가 언제 때렸는지 물어볼게요')
                q_pass = True
                step_pass = True
                
    
    return whentmp

# 언제
def __when__(who, place, screen):

    no_ans = '모르는 시간'
    temp = when_df.query('label == [0]').sample(n=5)
    temp = temp.loc[:, 'Q'].tolist()
    step_pass = False
    pass_cnt = 0

    for q in temp:
        if step_pass:
            break
        q = q.replace('{tag_people}', who).replace('{tag_place}', place)
        print(q)
        q_pass = False
        while not q_pass:
            ans = YNanswer(screen)
            if ans == '네':
                q_pass = True
                step_pass = True
                print(ans)
            elif ans == '아니요':
                print(ans)
                pass_cnt += 1
                if pass_cnt == 2:
                    return no_ans
                elif q == temp[-1]:
                    print('기억이 나지 않나 보네요.\n괜찮습니다. 나중에라도 기억이 나면 알려주세요.')   
                    return no_ans                   
                print('장애인 분을 위해서'+who+'(이)가 언제 때렸는지 확실하게 알 필요가 있어요.\
                    \n질문이 이해가 안 가시면 잘 모르겠다고 답해주세요/\
                    \n기억이 나지 않는다면 한 번 더 아니오를 눌러주세요.\
                    \n아니오를 한 번 더 누르면 다음 질문을 할게요.')
                print('질문을 다르게 해볼게요.')
                q_pass = True
            elif '잘 모르겠' in ans:
                print('잘 모르겠어요')
                print('질문을 다르게 해볼게요.')
                q_pass = True
                
        if q == temp[-1] and step_pass == False:
            print('기억이 나지 않나 보네요.\n괜찮습니다. 나중에라도 기억이 나면 알려주세요.')
            return no_ans

    temp = when_df.query('label == [1]').sample(n=5)
    temp = temp.loc[:, 'Q'].tolist()
    step_pass = False

    for q in temp:
        if step_pass:
            break
        q_pass = False
        q = q.replace('{tag_people}', who).replace('{tag_place}', place)
        print(q)
        step_pass = False
        while not q_pass:
            ans = SPanswer(screen)

            if '잘 모르겠' in ans:
                print('잘 모르겠어요')
                print('질문을 다르게 해볼게요.')
                q_pass = True
                
            else:
                print(ans)
                ans_pass = __anschk__(ans, entity_time)
                if ans_pass:
                    whentmp = ans
                elif not ans_pass:
                    print("'시간' 항목에서 답변해주세요.")
                    print('질문을 다시 할게요.')
                    continue
                print(who,'(이)가 ',place,'에서 장애인님을 때렸군요. 때린 시간은 ',whentmp,'(이)였구요\
                    \n이제부터',who,'가 무엇으로 때렸는지 물어볼게요')
                q_pass = True
                step_pass = True

    return whentmp

#재입력 기능
def __check__(who, place, when, what, where):
    chksen = who+'가 '+place+'에서 '+when+'에 '+what+'으로 장애인님의 '+where+'를 때린게 맞나요?'
    print(chksen)
    step_pass = False
    while not step_pass:
        ans = input()
        print(ans)
        if ans == '네':
            print('신고가 정상적으로 접수되었습니다. 금방 연락을 드릴게요.')
            step_pass = True
            return who, place, when, what, where, True
        elif ans == '아니오':
            print('어디가 틀린건지 얘기해주세요.')
            wrong = input()
            fix_list = wrong.split(' ')
            for i in fix_list:
                if i == '누가':
                    who = __who__()
                if i == '어디서':
                    place = __place__(who)
                if i == '언제':
                    when = __when__(who, place)
                if i == '무엇으로':
                    what = __what__(who, place, when)
                if i == '어디를':
                    where = __where__(who, place, when, what)
            return who, place, when, what, where, False

