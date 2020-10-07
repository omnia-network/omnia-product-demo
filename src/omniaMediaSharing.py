class OmniaMediaSharing:

    def __init__(self):
        self.userMedia = {}

        '''
        userMedia = {
            "username": {
                "text": "sometext",
                "image": "someimage",
                ...
            },
            "another_username":{
                ...
            },
            ...
        }
        '''
    
    def getText(self, username):
        if username in self.userMedia:
            return self.userMedia[username]["text"]
        else:
            return ''
    
    def setText(self, text, username):
        if username in self.userMedia:
            self.userMedia[username]["text"] = text
        else:
            self.userMedia.__setitem__(username, {"text": text})
    
    def addToText(self, text, username):
        if username in self.userMedia and "text" in self.userMedia[username]:
            self.userMedia[username]["text"] += text
        else:
            self.setText(text, username)
        
        print(self.userMedia[username]["text"])
    
    def removeFromText(self, nChar, username):
        if username in self.userMedia:
            if "text" in self.userMedia[username]:
                self.userMedia[username]["text"] = self.userMedia[username]["text"][:-nChar]

    def setAttribute(self, username, attribute, value=''):
        if username in self.userMedia:
            self.userMedia[username][attribute] = value
        else:
            self.userMedia.__setitem__(username, {attribute: value})
    
    def getAttribute(self, username, attribute):
        if username in self.userMedia:
            if attribute in self.userMedia[username]:
                return self.userMedia[username][attribute]
            else:
                print("attribute '{}' not found for user {}".format(attribute, username))
                return None
        else:
            print("user '{}' not found".format(username))