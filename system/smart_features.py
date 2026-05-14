"""
Smart Features for PriVox AI Assistant
Weather, emotional intelligence, and smart responses
"""
import json
import time
import datetime
import random
import webbrowser
import requests
from pathlib import Path
import platform
import subprocess
import os

class SmartFeatures:
    def __init__(self):
        self.system = platform.system()
        self.home_dir = str(Path.home())
        self.data_file = Path("data/user_preferences.json")
        self.load_preferences()
        
        # Music/search history
        self.search_history = self.preferences.get('search_history', [])
        
        # Weather cache
        self.weather_cache = None
        self.weather_cache_time = 0
        
    def load_preferences(self):
        """Load user preferences"""
        self.data_file.parent.mkdir(exist_ok=True)
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    self.preferences = json.load(f)
            except:
                self.preferences = {}
        else:
            self.preferences = {}
    
    def save_preferences(self):
        """Save user preferences"""
        with open(self.data_file, 'w') as f:
            json.dump(self.preferences, f, indent=2)
    
    def add_search(self, query):
        """Add search to history"""
        if query and query not in self.search_history:
            self.search_history.insert(0, query)
            self.search_history = self.search_history[:10]  # Keep last 10
            self.preferences['search_history'] = self.search_history
            self.save_preferences()
    
    # ======================
    # WEATHER FEATURE (Open-Meteo API - NO KEY)
    # ======================
    
    def get_weather(self, location=None):
        """Get weather using Open-Meteo API (free, no API key)"""
        # Cache weather for 10 minutes
        current_time = time.time()
        if self.weather_cache and (current_time - self.weather_cache_time) < 600:
            return self.weather_cache
        
        try:
            # Get location (CHANGED: Default to Vijayawada instead of Chennai)
            if location and location != "auto":
                # Simple location lookup (with Vijayawada added)
                location_coords = {
                    "london": (51.5074, -0.1278),
                    "new york": (40.7128, -74.0060),
                    "tokyo": (35.6762, 139.6503),
                    "paris": (48.8566, 2.3522),
                    "mumbai": (19.0760, 72.8777),
                    "chennai": (13.0827, 80.2707),
                    "delhi": (28.7041, 77.1025),
                    "bangalore": (12.9716, 77.5946),
                    "vijayawada": (16.5062, 80.6480),  # ADDED
                    "guntur": (16.3076, 80.4375),      # ADDED
                    "vizag": (17.6868, 83.2185),       # ADDED (Visakhapatnam)
                    "hyderabad": (17.3850, 78.4867)    # ADDED
                }
                
                for loc_name, coords in location_coords.items():
                    if loc_name in location.lower():
                        lat, lon = coords
                        city = loc_name.title()
                        break
                else:
                    # DEFAULT CHANGED: Vijayawada instead of Chennai
                    lat, lon, city = 16.5062, 80.6480, "Vijayawada"  # Changed to Vijayawada
            else:
                # Try to get approximate location from IP
                try:
                    response = requests.get('https://ipapi.co/json/', timeout=3)
                    data = response.json()
                    lat = data.get('latitude', 16.5062)  # Changed to Vijayawada lat
                    lon = data.get('longitude', 80.6480) # Changed to Vijayawada lon
                    city = data.get('city', 'Vijayawada') # Changed to Vijayawada
                except:
                    # DEFAULT CHANGED: Vijayawada instead of Chennai
                    lat, lon, city = 16.5062, 80.6480, "Vijayawada"  # Changed to Vijayawada
            
            # Rest of the function remains the same...
            # Open-Meteo API call
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                'latitude': lat,
                'longitude': lon,
                'current_weather': True,
                'temperature_unit': 'celsius',
                'windspeed_unit': 'kmh',
                'timezone': 'auto'
            }
            
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            
            if 'current_weather' in data:
                current = data['current_weather']
                temp = current['temperature']
                windspeed = current['windspeed']
                weather_code = current['weathercode']
                
                # Get weather description
                description = self._get_weather_description(weather_code)
                
                # Get time of day
                current_hour = datetime.datetime.now().hour
                time_of_day = "morning" if 5 <= current_hour < 12 else \
                             "afternoon" if 12 <= current_hour < 17 else \
                             "evening" if 17 <= current_hour < 22 else "night"
                
                # Create friendly response
                response = f"🌤️ Weather in {city}:\n"
                response += f"• {description}\n"
                response += f"• Temperature: {temp}°C\n"
                response += f"• Wind: {windspeed} km/h\n"
                response += f"• Time: {time_of_day.title()}\n\n"
                
                # Add suggestions based on weather
                if weather_code in [0, 1, 2]:  # Clear/partly cloudy
                    response += "Great weather for outdoor activities! 😊"
                elif weather_code in [3, 45, 48]:  # Cloudy/foggy
                    response += "Good day for indoor work or reading. 📚"
                elif weather_code in [51, 53, 55, 61, 63, 65, 80, 81]:  # Rain
                    response += "Rainy day - perfect for cozy indoor activities! ☔"
                elif weather_code in [71, 73, 75, 85]:  # Snow
                    response += "Snowy weather - stay warm! ❄️"
                else:
                    response += "Have a wonderful day! 🌟"
                
                self.weather_cache = response
                self.weather_cache_time = current_time
                return response
            else:
                return "🌤️ Weather data is currently unavailable. Please try again later."
                
        except Exception as e:
            print(f"[Weather Error] {e}")
            return "🌤️ Weather service is temporarily unavailable. You can try 'open google' to check online."
    
    def _get_weather_description(self, code):
        """Convert weather code to description"""
        weather_map = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Rime fog",
            51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
            61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
            80: "Rain showers", 81: "Heavy rain showers", 85: "Snow showers"
        }
        return weather_map.get(code, "Unknown weather conditions")
    
    # ======================
    # SMART YOUTUBE SEARCH
    # ======================
    
    def smart_youtube_search(self, query):
        """Smart YouTube search with history tracking"""
        self.add_search(query)
        
        # Clean query
        clean_query = query.replace('play', '').replace('youtube', '').replace('video', '').strip()
        
        # Create YouTube search URL
        search_url = f"https://www.youtube.com/results?search_query={clean_query.replace(' ', '+')}"
        webbrowser.open(search_url)
        
        # Smart responses based on query
        responses = {
            "motivation": "🎯 Playing motivation videos to boost your productivity! You've got this! 💪",
            "music": "🎵 Playing your favorite music! Enjoy the rhythm and relax! 🎶",
            "study": "📚 Playing study music to help you focus and learn effectively!",
            "workout": "💪 Playing workout music to energize your exercise session!",
            "relax": "😌 Playing relaxing sounds to calm your mind and reduce stress.",
            "learn": "🧠 Playing educational content to expand your knowledge!",
            "comedy": "😂 Playing comedy videos to brighten your day with laughter!",
        }
        
        # Find matching category
        for category, response in responses.items():
            if category in query.lower():
                return response
        
        # Default response
        return f"🎬 Playing '{clean_query}' on YouTube. Enjoy!"
    
    # ======================
    # EMOTIONAL INTELLIGENCE
    # ======================
    
    def handle_emotion(self, text):
        """Handle emotional states with intelligent responses"""
        text_lower = text.lower()
        
        emotion_responses = {
            "tired": [
                "😴 I understand you're tired. How about some relaxing music or a short break?",
                "💤 Feeling tired? A 20-minute power nap can work wonders for your energy!",
                "🛌 When tired, try the 4-7-8 breathing technique: 4 seconds in, 7 hold, 8 out.",
                "🎵 Would you like me to play some calming ambient sounds to help you relax?"
            ],
            "stressed": [
                "😌 Stress is natural. Try the 5-4-3-2-1 grounding technique.",
                "🧘 How about a quick mindfulness break? Focus on your breath for 60 seconds.",
                "📝 Stress relief: List 3 things you're grateful for right now.",
                "🌊 Would you like some calming ocean sounds or white noise?"
            ],
            "happy": [
                "😊 Great to hear you're happy! Want to celebrate with some upbeat music?",
                "🌟 Happiness is contagious! Share your positive energy with someone today.",
                "🎨 Perfect time to tackle creative projects or learn something new!",
                "✨ Your positive mood can inspire others. Keep shining!"
            ],
            "bored": [
                "🤔 Boredom can spark creativity! Try learning a new skill or hobby.",
                "📺 How about exploring some educational documentaries on YouTube?",
                "🚶 Bored? Perfect time for a short walk or digital detox.",
                "🎮 I can suggest interesting games or brain teasers if you'd like."
            ],
            "angry": [
                "😤 Anger is a valid emotion. Try counting backwards from 10 slowly.",
                "🌬️ When angry, try deep breathing: 4 seconds in, hold 4, 4 seconds out.",
                "🖊️ Writing down what's bothering you can help process angry feelings.",
                "🎵 Would you like some calming instrumental music to soothe your mood?"
            ],
            "anxious": [
                "🫂 Anxiety can be overwhelming. Remember to breathe and take one moment at a time.",
                "🌳 The 5-4-3-2-1 technique: Name 5 things you see, 4 you feel, 3 you hear, 2 you smell, 1 you taste.",
                "📆 Breaking tasks into smaller steps can reduce anxiety about big projects.",
                "🎶 Calming music or nature sounds can help ease anxious thoughts."
            ]
        }
        
        # Find matching emotion
        for emotion, responses in emotion_responses.items():
            if emotion in text_lower:
                response = random.choice(responses)
                
                # Add action suggestion
                actions = {
                    "tired": "Playing relaxing music in the background...",
                    "stressed": "Suggesting a quick meditation break...",
                    "happy": "Playing upbeat celebration music...",
                    "bored": "Suggesting interesting content to explore...",
                    "angry": "Playing calming sounds to help cool down...",
                    "anxious": "Suggesting mindfulness exercises..."
                }
                
                if emotion in actions:
                    response += f"\n\n{actions[emotion]}"
                
                return response
        
        # Default response for emotional states
        if any(word in text_lower for word in ["feel", "feeling", "mood", "emotion"]):
            return "I'm here to help with your mood. Would you like music suggestions, relaxation techniques, or just someone to talk to?"
        
        return None
    
    # ======================
    # DAY PLANNER
    # ======================
    
    def get_daily_suggestions(self):
        """Get smart daily suggestions based on time and weather"""
        current_time = datetime.datetime.now()
        current_hour = current_time.hour
        
        # Get weather for context
        weather_response = self.get_weather()
        weather_lower = weather_response.lower()
        
        # Time-based suggestions
        time_suggestions = []
        if 5 <= current_hour < 12:  # Morning
            time_suggestions = [
                "☀️ Good morning! Perfect time for planning your day.",
                "📝 Morning is great for focused work. Try the Pomodoro technique.",
                "🏃 Consider some morning exercise to boost your energy.",
                "🍳 Have a healthy breakfast to fuel your brain."
            ]
        elif 12 <= current_hour < 17:  # Afternoon
            time_suggestions = [
                "🌤️ Afternoon energy dip? Try a 10-minute walk outside.",
                "💡 Perfect time for creative tasks or brainstorming sessions.",
                "🥗 Consider a light, healthy lunch to avoid afternoon slump.",
                "🎵 Some background music can boost afternoon productivity."
            ]
        elif 17 <= current_hour < 22:  # Evening
            time_suggestions = [
                "🌙 Evening wind-down. Consider some relaxing music.",
                "📖 Time to unwind with a good book or podcast.",
                "🧘 Perfect for reflection or light stretching exercises.",
                "🎮 Some leisure time can help you recharge."
            ]
        else:  # Night
            time_suggestions = [
                "🌜 Late night? Remember to get enough sleep for tomorrow!",
                "💤 Consider winding down with some calming sounds.",
                "📓 Journaling before bed can improve sleep quality.",
                "🚫 Reduce screen time to help your body prepare for sleep."
            ]
        
        # Weather-based suggestions
        weather_suggestions = []
        if any(word in weather_lower for word in ["rain", "drizzle"]):
            weather_suggestions = [
                "☔ Rainy day - perfect for cozy indoor activities!",
                "📚 Great weather for reading, learning, or creative projects.",
                "☕ How about a warm drink while you work?"
            ]
        elif any(word in weather_lower for word in ["sunny", "clear"]):
            weather_suggestions = [
                "😎 Beautiful day! Consider some outdoor time if possible.",
                "🌿 Sunny weather - great for vitamin D and mood boost!",
                "🏞️ Perfect for a short walk or outdoor break."
            ]
        elif any(word in weather_lower for word in ["hot", "warm"]):
            weather_suggestions = [
                "🔥 Hot day - stay hydrated and consider lighter activities.",
                "❄️ Keep cool with indoor tasks or air-conditioned spaces.",
                "🍹 Remember to drink plenty of water throughout the day."
            ]
        
        # Productivity tips
        productivity_tips = [
            "💡 Drinking water can boost cognitive performance by 30%.",
            "🚶 Short walks can improve creativity and problem-solving.",
            "🎶 Instrumental music can enhance concentration during work.",
            "⏰ The 52-17 rule: Work for 52 minutes, break for 17.",
            "📱 Digital detox for 30 minutes can refresh your mind.",
            "✍️ Writing down goals increases achievement probability by 42%."
        ]
        
        # Build response
        response = "📅 **Your Day Planner**\n\n"
        response += f"🕐 **Time:** {current_time.strftime('%I:%M %p')}\n"
        response += f"{weather_response.split('Weather')[0]}"
        
        response += "\n🎯 **Suggestions:**\n"
        response += f"1. {random.choice(time_suggestions)}\n"
        if weather_suggestions:
            response += f"2. {random.choice(weather_suggestions)}\n"
        response += f"3. {random.choice(productivity_tips)}\n"
        
        response += "\n🌟 **Remember:** Take breaks, stay hydrated, and be kind to yourself!"
        
        return response
    
    # ======================
    # SMART RESPONSES
    # ======================
    
    def get_smart_response(self, text):
        """Get smart response for common queries"""
        text_lower = text.lower()
        
        # Greetings
        if any(word in text_lower for word in ["hello", "hi", "hey", "greetings"]):
            greetings = [
                "Hello! How can I help you today? 😊",
                "Hi there! Ready to assist you with anything. 🚀",
                "Hey! What can I do for you? 💫",
                "Greetings! I'm here to help. 🌟"
            ]
            return random.choice(greetings)
        
        # Thanks
        if any(word in text_lower for word in ["thank", "thanks", "appreciate"]):
            thanks_responses = [
                "You're welcome! Happy to help. 😊",
                "Anytime! Let me know if you need anything else. 🌟",
                "Glad I could assist! 🚀",
                "My pleasure! 😄"
            ]
            return random.choice(thanks_responses)
        
        # Who are you
        if any(word in text_lower for word in ["who are you", "what are you", "your name"]):
            return "I'm PriVox, your privacy-first AI assistant! 🤖 I can help with system commands, weather, music, and more. All processing happens locally on your device for maximum privacy. 🔒"
        
        # What can you do
        if any(word in text_lower for word in ["what can you do", "capabilities", "features"]):
            capabilities = [
                "• Open apps (WhatsApp, YouTube, Calculator, etc.)",
                "• Take screenshots",
                "• Check weather",
                "• Play music/videos on YouTube",
                "• Open file manager and folders",
                "• Lock screen and system controls",
                "• Answer questions (using local AI)",
                "• Work completely offline",
                "• All with privacy-first design! 🔒"
            ]
            return "I can help you with:\n" + "\n".join(capabilities)
        
        # Time
        if any(word in text_lower for word in ["time", "what time"]):
            current_time = datetime.datetime.now().strftime("%I:%M %p")
            return f"🕐 The current time is {current_time}"
        
        # Date
        if any(word in text_lower for word in ["date", "today's date", "what day"]):
            current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
            return f"📅 Today is {current_date}"
        
        return None

# Global instance
smart_features = SmartFeatures()