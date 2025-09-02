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
        token = self.account_data['token']
        delay = self.account_data['delay']
        
        try:
            self.log("Starting TubeRocket worker...")
            self.update_status("Connecting")
            
            # Get account info
            head_get_info = {
                "Host": "tuberocket.app:3000",
                "token": token,
            }
            
            response = self.session.get("http://tuberocket.app:3000/api/member", headers=head_get_info)
            if response.status_code != 200:
                raise Exception(f"Failed to connect: {response.status_code}")
            
            get_info = response.json()
            email = get_info["result"]["email"]
            coin = get_info["result"]["coin"]
            
            self.update_status("Running", email, coin)
            self.log(f"Connected: {email} | Coins: {coin}")
            
            head_run_video = {
                "Host": "tuberocket.app:3000",
                "token": token,
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
