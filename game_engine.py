import random 
from difflib import SequenceMatcher
from nlp.wordnet_engine import WordNetEngine
from nlp.embedding_engine import EmbeddingEngine

class GameEngine:
    def __init__(self, data_path: str="data/word_bank.json"):
        print("Game Engine Initializing......")
        self.wordnet = WordNetEngine(data_path)
        self.score = 0
        self.total_rounds = 0

        self.word_pool = [                                                      #Here this var will store all the words from the json
            key for key in self.wordnet.data.keys()                             #But will remove all the synset ids attched to it
            if not key.endswith(("-n","-v","-a","-r","-s")) and len(key) > 1        #Descriptions and examples will also be saved and retained
        ]                                                                          #length is >1 as to not take single characters or numbers
        self.current_target = None
        self.primary_synset = None
        self.current_word_score = 0
        self.hints_revealed = 0
        self.total_score = 0
        


    def get_random_word(self) -> str | None:
        if not self.word_pool:
            return None

        for i in range(10):                                       #it will have 10 tries to get a word, a word having all senses, definition and examples
            word = random.choice(self.word_pool)                   # a random word will be chosen
            senses = self.wordnet.get_senses(word)
            if senses:
                return word

        return None

    def start_round(self) -> dict | None:
        target_word = self.get_random_word()                       # gets a random word from the word_pool

        if not target_word:                                               # even after 10 tries, it gets a word with no valid senses
            print("Error: Could not retrieve a valid word for the round. ")   # or path is incorrect. In that case the starting condition on word_pool fails 
            return None

        self.current_target = target_word
        senses = self.wordnet.get_senses(target_word)
        self.primary_synset = senses[0]
        self.current_word_score = len(target_word) * 10
        self.hints_revealed = 0

        return {
            "word_length" : len(target_word),
            "potential_score" : self.current_word_score
        }

    def request_hint(self) -> str:
        if not self.current_target:
            return "No target Word. Start a New Round.."

        self.hints_revealed += 1

        if self.hints_revealed == 1:
            self.current_word_score = max(5,int(self.current_word_score*0.7))
            defintion = self.wordnet.get_definition(self.primary_synset)
            return f"HINT (Definition): {defintion or 'NO Definition found.'}"

        examples = self.wordnet.get_examples(self.primary_synset)
        example_index = self.hints_revealed - 2

        if examples and example_index > len(examples):
            self.current_word_score = max(5,int(self.current_word_score*0.8))
            masked_examples = examples[example_index].lower().replace(self.current_target, "_______")
            return f"HINT (example): {masked_examples}"

        return "No more hints available for this word!"

    def check_guess(self,user_guess : str) -> dict:
        guess = user_guess.strip().lower()
        target = self.current_target.lower()

        if guess == self.current_target:
            earnedpoints = self.current_word_score
            self.total_score += earnedpoints
            return {
                "status" : "correct",
                "similarity_pst" : 100.0,
                "earned_score" : earnedpoints,
                "total_score" : self.total_score
            }

        similarity = SequenceMatcher(None, guess, target).ratio() * 100
        if similarity >= 80:
            closeness = "Very Close!"
        elif similarity >= 50:
            closeness = "Close"
        else:
            closeness = "Far"

        return {
            "status" : "incorrect",
            "closeness" : closeness,
            "similarity_pct" : round(similarity, 1)
        }

## ------TEsting ___-----

if __name__ == "__main__":
    game= GameEngine()
    print("Commands: 'hint' for clues | 'skip' for give up | 'quit' for exit\n")

    while True:
        round_info = game.start_round()
        if not round_info:
            print("Failed to start round")
            break

        print(f"NEW WORD LOADED. Length: {round_info['word_length']} letters")
        print(f"MAX POTENTIAL SCORE for this word: {round_info['potential_score']} points")

        while True:
            action = input(f"\n[{game.current_target[0]}... ({round_info['word_length']} letters) Score Value: {game.current_word_score}]\n Your Guess > ")
            

            if action in ["exit", "quit"]:
                print(f"Final score: {game.total_score}. Thanks for playing!")
                exit()

            if action == "skip":
                print(f"Given up! The target Word was: '{game.current_target}'")
                print(f"Current Total Score: {game.total_score}")
                break

            if action == "hint":
                hint_text = game.request_hint()
                print(f"--> {hint_text}")
                continue

            result = game.check_guess(action)

            if result["status"] == "correct":
                print(f"CORRECT! You earned {result['earned_score']} points!")
                print(f"Total cumilative Score : {result['total_score']}")
                break
            else:
                print(f"--> WRONG! Feedback: {result['closeness']} ({result['similarity_pct']}% match)\n Keep Trying!")
            