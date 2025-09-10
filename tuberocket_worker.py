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
        self.real_token = account_data.get('token', '')  # Get existing token
        
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
    
    def perform_signin(self):
        """Perform sign-in to get/refresh real token"""
        token_signin = self.account_data.get('token_signin', '')
        
        if not token_signin:
            raise Exception("No sign-in token provided!")
        
        version_code = self.account_data.get('version_code', 187)
        android = self.account_data.get('android', 29)
        device = self.account_data.get('device', '')
        locale = self.account_data.get('locale', 'VN')
        device_token = self.account_data.get('device_token', '')
        
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

        self.log("Performing sign-in to get/refresh token...")
        response_signin = self.session.post("http://tuberocket.app:3000/api/signin", headers=head_sign_in)
        
        if response_signin.status_code != 200:
            raise Exception(f"Sign-in failed: HTTP {response_signin.status_code}")
        
        signin_data = response_signin.json()
        
        if signin_data.get("retMessage") != "Success!!":
            raise Exception(f"Sign-in failed: {signin_data.get('retMessage', 'Unknown error')}")
        
        # Get the real token from response
        self.real_token = signin_data["result"]["token"]
        youtube_api_key = signin_data["result"].get("youtube_api_key", "")
        
        self.log(f"Sign-in successful. Got real token: {self.real_token[:10]}...")
        
        # Update token in database
        if self.callback:
            self.callback(self.account_data['id'], 'update_token', self.real_token)
        
        return self.real_token
    
    def test_token_validity(self):
        """Test if current token is still valid by calling member API"""
        if not self.real_token:
            return False
        
        try:
            head_get_info = {
                "Host": "tuberocket.app:3000",
                "token": self.real_token,
            }
            
            response = self.session.get("http://tuberocket.app:3000/api/member", headers=head_get_info)
            status = response.json().retMessage
            if(status != "Token Invalid"):
                return True
            return False
            
        except:
            return False
    
    def run(self):
        account_id = self.account_data['id']
        delay = self.account_data['delay']
        
        try:
            self.log("Starting TubeRocket worker...")
            self.update_status("Connecting")
            
            # Check if we have real token and test it first
            if self.real_token:
                self.log("Found existing real token, testing validity...")
                self.update_status("Checking Token")
                if self.test_token_validity():
                    self.log("Existing real token is valid, using it")
                else:
                    self.log("Existing real token is invalid or expired")
                    self.real_token = None
            
            # Get new token only if needed
            if not self.real_token:
                self.log("No valid real token, performing sign-in...")
                self.update_status("Signing In")
                self.real_token = self.perform_signin()
            
            # Update headers with real token
            head_get_info = {
                "Host": "tuberocket.app:3000",
                "token": self.real_token,
            }
            
            self.update_status("Getting Account Info")
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
                "token": self.real_token,
                "Content-Length": "71",
                "Content-Type": "application/json; charset=UTF-8",
            }
            
            video_count = 0
            consecutive_errors = 0
            max_consecutive_errors = 3
            
            while not self.stop_event.is_set():
                try:
                    # Get video
                    self.update_status("Getting Video", email, coin)
                    response = self.session.get("http://tuberocket.app:3000/api/video", headers=head_get_info)
                    
                    # Check if token expired/invalid
                    if response.status_code in [401, 403]:
                        self.log("Token appears to be expired/invalid, refreshing...")
                        self.update_status("Refreshing Token", email, coin)
                        try:
                            self.real_token = self.perform_signin()
                            # Update headers with new token
                            head_get_info["token"] = self.real_token
                            head_run_video["token"] = self.real_token
                            # Retry getting video
                            response = self.session.get("http://tuberocket.app:3000/api/video", headers=head_get_info)
                        except Exception as refresh_error:
                            self.log(f"Failed to refresh token: {refresh_error}")
                            raise refresh_error
                    
                    if response.status_code != 200:
                        raise Exception(f"Failed to get video: {response.status_code}")
                    
                    get_video = response.json()
                    
                    # Check if response indicates token issue
                    if get_video.get("retCode") != 0 and "token" in str(get_video.get("retMessage", "")).lower():
                        self.log("API response indicates token issue, refreshing...")
                        self.update_status("Token Invalid - Refreshing", email, coin)
                        try:
                            self.real_token = self.perform_signin()
                            head_get_info["token"] = self.real_token
                            head_run_video["token"] = self.real_token
                            continue  # Retry the loop
                        except Exception as refresh_error:
                            self.log(f"Failed to refresh token: {refresh_error}")
                            raise refresh_error
                    
                    id_video = get_video["result"]["videoId"]
                    time_video = get_video["result"]["playSecond"]
                    
                    self.log(f"Processing video {id_video} - Wait {time_video} seconds")
                    self.update_status(f"Processing Video ({time_video}s)", email, coin)
                    
                    # Reset error counter on successful video fetch
                    consecutive_errors = 0
                    
                    # Wait for video duration with randomization
                    random_delay = random.uniform(0.8, 1.2)  # 80% to 120% of original time
                    actual_wait = int(time_video * random_delay)
                    
                    for i in range(actual_wait, 0, -1):
                        if self.stop_event.is_set():
                            return
                        # Update countdown status
                        self.update_status(f"Watching Video ({i}s left)", email, coin)
                        time.sleep(1)
                    
                    # Receive coin
                    self.update_status("Submitting Video", email, coin)
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
                    
                    # Handle token issues in submit video API
                    if response.status_code in [401, 403]:
                        self.log("Token expired during video submission, refreshing...")
                        self.update_status("Token Expired - Refreshing", email, coin)
                        try:
                            self.real_token = self.perform_signin()
                            head_get_info["token"] = self.real_token
                            head_run_video["token"] = self.real_token
                            # Retry submission
                            response = self.session.put(
                                "http://tuberocket.app:3000/api/video",
                                headers=head_run_video,
                                json=data_receive_coin,
                            )
                        except Exception as refresh_error:
                            self.log(f"Failed to refresh token during submission: {refresh_error}")
                            raise refresh_error
                    
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
                        for i in range(random_wait, 0, -1):
                            if self.stop_event.is_set():
                                return
                            self.update_status(f"Waiting ({i}s)", email, received_coin)
                            time.sleep(1)
                
                except Exception as e:
                    error_msg = str(e)
                    consecutive_errors += 1
                    self.log(f"Error processing video (attempt {consecutive_errors}): {error_msg}")
                    
                    # Check for permanent account issues
                    if any(keyword in error_msg.lower() for keyword in ['banned', 'suspended', 'blocked']):
                        self.update_status("Error - Account Banned")
                        self.log("Account appears to be banned!")
                        break
                    
                    # If too many consecutive errors, try refreshing token
                    if consecutive_errors >= max_consecutive_errors:
                        self.log(f"Too many consecutive errors ({consecutive_errors}), attempting token refresh...")
                        self.update_status("Error - Refreshing Token")
                        try:
                            self.real_token = self.perform_signin()
                            head_get_info["token"] = self.real_token
                            head_run_video["token"] = self.real_token
                            consecutive_errors = 0  # Reset counter after successful refresh
                            self.log("Token refreshed successfully, continuing...")
                        except Exception as refresh_error:
                            self.log(f"Failed to refresh token after errors: {refresh_error}")
                            self.update_status("Error - Token Refresh Failed")
                            break
                    else:
                        self.update_status(f"Error - Retrying ({consecutive_errors}/{max_consecutive_errors})")
                    
                    # Wait before retry
                    if not self.stop_event.is_set():
                        wait_time = min(10 * consecutive_errors, 60)  # Exponential backoff, max 60s
                        self.log(f"Waiting {wait_time} seconds before retry...")
                        for i in range(wait_time, 0, -1):
                            if self.stop_event.is_set():
                                return
                            self.update_status(f"Error - Retry in {i}s")
                            time.sleep(1)
        
        except Exception as e:
            self.log(f"Connection error: {str(e)}")
            if "token" in str(e).lower() and any(word in str(e).lower() for word in ['invalid', 'expired']):
                self.update_status("Error - Token Invalid")
            else:
                self.update_status("Error - Connection Failed")
        
        finally:
            if not self.stop_event.is_set():
                self.update_status("Stopped")
            self.log("Worker stopped")
