"""Every spoken line in Letter Trucks v2. Writes lines.json (key -> text).
The same text is used for TTS generation and for the browser-voice fallback."""
import json, os

WORDS = dict(a='apple', b='bus', c='cat', d='dog', e='egg', f='fish', g='goat', h='horse', i='igloo', j='juice',
             k='key', l='lion', m='moon', n='nose', o='octopus', p='pig', q='queen', r='rocket', s='sun', t='turtle',
             u='umbrella', v='van', w='watermelon', x='fox', y='yarn', z='zebra')

# how the letter's sound is written so the voice says the sound, not the letter name.
# stutter style: the voice repeats the first sound of the word, which keeps it the right sound.
SOUND = {l: f"{l}-{l}-{w}" for l, w in WORDS.items()}
SOUND.update(c='k-k-cat', q='kw-kw-queen', x='fox, ks, ks', g='g-g-goat',
             e='eh-eh-egg', i='ih-ih-igloo', o='ah-ah-octopus', u='uh-uh-umbrella')

def lines():
    L = {}
    for l, w in WORDS.items():
        U = l.upper()
        s = SOUND[l]
        L[f'box_{l}'] = f"I'm {U}! {s}!"
        L[f'wrong_{l}'] = f"I'm little {U}! {s}!"
        L[f'right_{l}'] = f"Little {U}! {s}!"
        L[f'meet_{l}'] = f"Big {U} and little {U}! {s}!"
    L.update({
        'intro_deliver': "The bears need letters! Let's go!",
        'deliver_done': "Every bear got a letter! Hooray!",
        'intro_tow': "Let's go towing!",
        'tow_done': "Great towing! Beep beep!",
        'menu_deliver': "Bear deliveries!",
        'menu_tow': "Tow truck!",
        'title': "Letter Trucks!",
    })
    L.update(bear_lines())
    return L

BEAR_VOICE = 'Leda'
def bear_lines():
    B = {}
    for l, w in WORDS.items():
        U = l.upper(); s = SOUND[l]
        B[f'order0_{l}'] = f"I need the letter {U}! {s}!"
        B[f'order1_{l}'] = f"I need {s}!"
        B[f'yay_{l}'] = f"Yay! {'Double U' if l == 'w' else U}! {s}!"
        B[f'say_{l}'] = f"Can you say {s}?"
        # "little D" / "little P" alone trip the voice provider's content filter
        B[f'where_{l}'] = f"Where's my little letter {U}?" if l in 'dpfh' else f"Where's my little {U}?"
    B.update({'thanks': "Thank you!", 'thanks2': "Thank you so much!", 'great': "You did it!",
              'react_yum': "Yum yum!", 'react_wow': "Wow!", 'react_love': "I love it!", 'react_whee': "Whee!", 'react_brrr': "Brrr! So cold!"})
    return B

def voices():
    return {k: BEAR_VOICE for k in bear_lines()}

if __name__ == '__main__':
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lines.json')
    json.dump(lines(), open(out, 'w'), indent=1)
    json.dump(voices(), open(out.replace('lines.json', 'voices.json'), 'w'), indent=1)
    print(len(lines()), 'lines ->', out)
