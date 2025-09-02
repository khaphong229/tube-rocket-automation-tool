import requests
import time
import random
from threading import Thread, Event

class TubeRocketWorker(Thread):
    def __init__(self, account_data, callback_func, stop_event):
        super().__init__()
        self.account_data = account_data
        self.callback = callback_func
        self.stop_event = stop_event
        self.session = requests.Session()
        self.daemon = True
        
        # Setup proxy if provided
        if account_data['proxy']:
            self.session.proxies = {
                'http': account_data['proxy'],
                'https': account_data['proxy']
            }
    
    def log(self, message):
        if self.callback:
            self.callback(self.account_data['id'], 'log', message)
    
    def update_status(self, status, email=None, coin=None):
        if self.callback:
            self.callback(self.account_data['id'], 'status', {
                'status': status,
                'email': email,
                'coin': coin
            })
    
    def run(self):
        account_id = self.account_data['id']
        token_signin = self.account_data.get('token_signin', '')
        
        if not token_signin:
            self.log("Error: No sign-in token provided!")
            self.update_status("Error - No Sign-in Token")
            return
        
        version_code = self.account_data.get('version_code', 187)
        android = self.account_data.get('android', 29)
        device = self.account_data.get('device', '')
        locale = self.account_data.get('locale', 'VN')
        device_token = self.account_data.get('device_token', '')
        delay = self.account_data['delay']
        
        try:
            self.log("Starting TubeRocket worker...")
            self.update_status("Connecting")

            # Sign-in to get real token
            head_sign_in = {
                "Host": "tuberocket.app:3000",
                "token": token_signin,
                "versionCode": str(version_code),
                "android": str(android),
                "device": device,
                "locale": locale,
                "deviceToken": device_token,
                "Content-length": "0",
            }

            self.log("Performing sign-in...")
            response_signin = self.session.post("http://tuberocket.app:3000/api/signin", headers=head_sign_in)
            
            if response_signin.status_code != 200:
                raise Exception(f"Sign-in failed: HTTP {response_signin.status_code}")
            
            signin_data = response_signin.json()
            
            if signin_data.get("retMessage") != "Success!!":
                raise Exception(f"Sign-in failed: {signin_data.get('retMessage', 'Unknown error')}")
            
            # Get the real token from response
            real_token = signin_data["result"]["token"]
            youtube_api_key = signin_data["result"].get("youtube_api_key", "")
            
            self.log(f"Sign-in successful. Got real token: {real_token[:10]}...")
            
            # Update token in database
            if self.callback:
                self.callback(self.account_data['id'], 'update_token', real_token)
            
            # Get account info using real token
            head_get_info = {
                "Host": "tuberocket.app:3000",
                "token": real_token,
            }
            
            response = self.session.get("http://tuberocket.app:3000/api/member", headers=head_get_info)
            if response.status_code != 200:
                raise Exception(f"Failed to get member info: {response.status_code}")
            
            get_info = response.json()
            email = get_info["result"]["email"]
            coin = get_info["result"]["coin"]
            
            self.update_status("Running", email, coin)
            self.log(f"Connected: {email} | Coins: {coin}")
            
            head_run_video = {
                "Host": "tuberocket.app:3000",
                "token": real_token,
                "Content-Length": "71",
                "Content-Type": "application/json; charset=UTF-8",
            }
            
            video_count = 0
            
            while not self.stop_event.is_set():
                try:
                    # Get video
                    response = self.session.get("http://tuberocket.app:3000/api/video", headers=head_get_info)
                    if response.status_code != 200:
                        raise Exception(f"Failed to get video: {response.status_code}")
                    
                    get_video = response.json()
                    id_video = get_video["result"]["videoId"]
                    time_video = get_video["result"]["playSecond"]
                    
                    self.log(f"Processing video {id_video} - Wait {time_video} seconds")
                    
                    # Wait for video duration with randomization
                    random_delay = random.uniform(0.8, 1.2)  # 80% to 120% of original time
                    actual_wait = int(time_video * random_delay)
                    
                    for i in range(actual_wait, 0, -1):
                        if self.stop_event.is_set():
                            return
                        time.sleep(1)
                    
                    # Receive coin
                    data_receive_coin = {
                        "id": id_video,
                        "playCount": 0,
                        "playSecond": 0,
                        "boost": 0,
                        "status": "",
                    }
                    
                    response = self.session.put(
                        "http://tuberocket.app:3000/api/video",
                        headers=head_run_video,
                        json=data_receive_coin,
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Failed to submit video: {response.status_code}")
                    
                    receive = response.json()
                    received_coin = receive["result"]["coin"]
                    video_count += 1
                    
                    self.log(f"#{video_count} | Video {id_video} | Coins: {received_coin}")
                    self.update_status("Running", email, received_coin)
                    
                    # Update stats in callback
                    if self.callback:
                        self.callback(self.account_data['id'], 'stats', {
                            'videos': video_count,
                            'coins': received_coin
                        })
                    
                    # Random delay between videos
                    if not self.stop_event.is_set():
                        random_wait = random.randint(delay, delay + 3)
                        time.sleep(random_wait)
                
                except Exception as e:
                    error_msg = str(e)
                    self.log(f"Error processing video: {error_msg}")
                    
                    if any(keyword in error_msg.lower() for keyword in ['banned', 'expired', 'unauthorized']):
                        self.update_status("Error - Token Invalid")
                        self.log("Account banned or token expired!")
                        break
                    
                    # Wait before retry
                    if not self.stop_event.is_set():
                        time.sleep(10)
        
        except Exception as e:
            self.log(f"Connection error: {str(e)}")
            self.update_status("Error")
        
        finally:
            if not self.stop_event.is_set():
                self.update_status("Stopped")
            self.log("Worker stopped")
