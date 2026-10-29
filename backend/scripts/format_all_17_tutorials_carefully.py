import os
import sys
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SyncSessionLocal
from models.learner_pack import TutorialContent
from models.tutorial import Tutorial

def clean_spacing(text):
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# --- TUTORIAL 1: Origin of Emotions ---
def format_tut_1(text):
    return """## 1. What is it?

**Emotions are signals.** They tell us how we feel about what is happening around us and within us, and they give us the energy to respond.

When someone asks _“How are you?”_, most of us instinctively say _“I’m fine”_ and move on. We rarely stop to notice what we actually feel. This course begins with that pause.

The word emotion comes from the Latin root **_emovere_**, which means _“to move”_. This tells us what emotions fundamentally do: **they move us to act**:
* **Fear** moves us to run from danger or prepare for a threat.
* **Sadness** moves us to slow down and reach out for comfort.
* **Anger** gives us the energy to stand up for ourselves and protect what matters.

> 🧭 **The Compass Metaphor:**
> Emotions are like a compass. A compass does not make the journey for you—it only shows you the direction. Emotions work the exact same way: they point to what matters in a situation, so that you can consciously decide what to do.

### Evolutionary Roots
Emotions have an ancient evolutionary history. Thousands of years ago, people lived in small hunter-gatherer bands, and emotions directly ensured survival:
* **Fear** kept early humans alert to predators and environmental hazards.
* **Happiness** brought them together over shared food and bonded the tribe.
* **Sadness** led them to seek comfort from one another after a painful loss.
* **Anger** provided the fierce energy required to protect the group from harm.

Our daily lives look very different today, but we carry the exact same biology—and our emotions perform the exact same essential jobs.

---

## 2. How Emotions Show Up

Every tutorial in this module shows how an emotion appears across three core dimensions:

| Dimension | What to Notice | Real-Life Example |
| :--- | :--- | :--- |
| 🧠 **Thoughts** | What runs through your mind | _“What if I mess this up?”_ |
| 💓 **Body** | What you feel physically | A racing heart, a heavy chest, butterflies in the stomach |
| 🏷️ **Feelings** | The name of the emotion itself | Nervous, lonely, proud, frustrated |

> 💡 **Key Takeaway:**
> Learning to notice all three is the foundational skill of this course. Often, the body reacts first—before the conscious mind can even name the feeling.
>
> **Emotions are neither good nor bad.** We often label happiness “good” and anger or fear “bad”, but every emotion carries valuable information. When we listen to its message and respond skillfully, the emotion naturally fades. Difficulties arise only when we suppress the message, push it away, or act impulsively without thinking.

---

## 3. What Does Research Say?

#### A. Basic emotions are hardwired across human cultures
In 1971, psychologists **Paul Ekman and Wallace Friesen** worked with the Fore people of Papua New Guinea—a community with virtually zero exposure to films or modern media. Participants listened to stories describing emotional situations and matched them with photographs of facial expressions. Both adults and children identified expressions with striking accuracy, proving that basic emotions are universal biological features of our species.

> _Note:_ Alternative perspectives, such as psychologist **Lisa Feldman Barrett’s** theory of constructed emotion, emphasize that cultural context and language deeply shape how we categorize and articulate these signals.

#### B. Naming a feeling calms down the brain
In a landmark 2007 **UCLA brain-imaging study**, Matthew Lieberman and colleagues discovered that when individuals put their feelings into words (**_affect labeling_**):
* Neural activity dropped dramatically in the **amygdala** (the brain's alarm bell).
* Neural activity increased in the **prefrontal cortex** (the rational planning center).
* _Putting feelings into language acts as an automatic biological brake on emotional intensity._

#### C. Emotional granularity protects mental health
Researchers **Todd Kashdan, Lisa Feldman Barrett, and Patrick McKnight** found that individuals with high *emotional granularity*—people who distinguish specific feelings (saying _“disappointed”_ or _“overwhelmed”_ rather than just _“bad”_):
* Cope significantly better with acute stress.
* Are less likely to resort to self-destructive habits or lash out at others.
* Recover baseline calm much faster.

---

## 4. Case Study: An Everyday Example

**Kavya** started her first job at a bank in Pune three months ago. Every Sunday, her mother calls from Madurai and asks, _“How are you?”_ And every Sunday, Kavya automatically says, _“Fine, Amma.”_

One Sunday, after hanging up, she pauses and asks herself the question honestly:
* 🧠 **Thoughts:** _“I don’t know anyone here. Everyone at work already has their own tight group.”_
* 💓 **Body:** She has felt exhausted all week despite sleeping 8 hours. She has stopped cooking dinner and only eats instant snacks.
* 🏷️ **Feelings:** She tries a few labels. Bored? No. Tired? Partly. Then she finds the exact word: **lonely**.

**The Turning Point:**
_“Fine”_ gave her nothing to act on, but **_“lonely”_** gave her a clear direction. That evening, she messaged a colleague about joining the bank’s badminton club. The next Sunday, she answered her mother with the truth.

---

## 5. Think About It (Self-Reflection)

* 💭 **When did you last say “I’m fine” when you were not?** What were you actually experiencing deep down?
* 💭 **Which do you usually notice first when an emotion arises:** your thoughts, your physical body sensations, or the emotional label?
* 💭 **Recall a time an “unpleasant” emotion helped you.** What was its signal warning you about?
"""

# --- TUTORIAL 2: Understanding Fear ---
def format_tut_2(text):
    return """## 1. What is it?

**Fear is an alarm system.** It warns us of danger and mobilizes the entire body to deal with an immediate threat.

Its fundamental biological message is simple:
> ⚡ **Core Message:** _“Something important is at stake. Get ready.”_

For early humans, the danger was a predator or rival tribe. Today, the danger is rarely a tiger; it is an exam, a job interview, a difficult conversation, or moving to an unfamiliar city. The external trigger has evolved, but our biological hardware responds the exact same way.

### What Happens in Your Body
When your sensory organs perceive a threat, a small almond-shaped brain structure called the **amygdala** sounds the alarm. Within fractions of a second:
* The brain signals the adrenal glands to flood the bloodstream with **adrenaline** and **cortisol**.
* Your heart pumps faster, sending oxygenated blood to large skeletal muscles.
* Breathing becomes rapid and shallow.
* Blood diverts away from digestion, causing “butterflies” or a hollow feeling in the stomach.

---

## 2. Freeze, Run, or Fight

Early humans survived dangers through three distinct reactions, which show up in modern life:

| Primitive Reaction | What It Looks Like Today | Modern Academic / Work Example |
| :--- | :--- | :--- |
| 🧊 **Freeze** | Mind goes completely blank | Staring at an exam question and forgetting formulas you practiced |
| 🏃 **Run** | Avoidance and procrastination | Putting off studying, canceling meetings, scrolling social media |
| 🥊 **Fight** | Irritability and defensiveness | Snapping aggressively at roommates or teammates under pressure |

### Using Fear Productively
A moderate amount of fear sharpens focus and pushes you to prepare. In the tutorial, **Raja** studied harder and accepted **Gopi’s** help precisely because he respected the challenge. Fear becomes harmful only when it leads to total avoidance.

#### Three Strategies to Regulate Fear:
1. 🏷️ **Name it clearly:** Saying _“I am terrified of failing this presentation”_ gives your prefrontal cortex something specific to address, unlike a vague cloud of anxiety.
2. 🪜 **Break it into micro-steps:** Raja and Gopi studied step-by-step over three evenings. Each small successful step shrinks the perceived mountain.
3. 🤝 **Share it with someone you trust:** Fear grows in isolation and shrinks in conversation.

---

## 3. What Does Research Say?

#### A. The fear response is designed for action
**Harvard Medical School** researchers explain that when the amygdala triggers the autonomic nervous system, extra oxygen reaches the brain, sight sharpens, and reaction times drop. A racing heart before an exam is **not a sign of weakness**—it is your body actively powering up to perform.

#### B. Reappraising anxiety as excitement
In a famous study by **Alison Wood Brooks at Harvard Business School**, participants were assigned stressful tasks (public speaking, solving complex mathematics under time pressure, and singing karaoke):
* One group was told to say: _“I am calm.”_
* Another group was told to say: _“I am excited.”_
* In the karaoke test, those who framed their arousal as **excitement** scored **80%**, while those trying to force calm scored **69%**, and those saying _“I am anxious”_ scored **53%**.
* _Trying to suppress an adrenaline surge is exhausting; channeling high arousal into excitement works with your biology._

#### C. Social support alters physical perception
In a 2008 **University of Virginia study by Simone Schnall**, participants were asked to estimate the steepness of a grueling hill:
* Participants standing **next to a friend** estimated the hill to be significantly less steep than those standing alone.
* Simply visualizing a supportive friend produced a measurable reduction in perceived difficulty.
* _Having an ally changes how difficult a challenge looks to your brain._

---

## 4. Case Study: An Everyday Example

**Farhan** is a second-year engineering student in Lucknow who realized his genuine passion is user interface design. He has wanted to discuss switching courses with his father for two months:
* 🧠 **Thoughts:** _“Abbu will be crushed. What if he refuses? What will the extended family say?”_
* 💓 **Body:** Chest tightness, sleeplessness, churning stomach. He starts staying at the campus library late just to avoid dinner discussions.
* 🏷️ **Feelings:** Anxious, cornered, and guilty for concealing his plans.

**The Turning Point:**
Farhan recognized that avoidance was the **“run”** response—it kept his fear perpetually alive without solving anything. He decided to treat fear as a signal to prepare:
1. He confided in his cousin first and rehearsed the conversation aloud.
2. He compiled concrete data on accredited design colleges, career placement records, and fee structures.
3. On a quiet Sunday, he told his father: _“I feel nervous bringing this up because your respect matters to me, but I have researched this thoroughly.”_

His father asked for a week to review the numbers. Farhan’s heart was still beating fast, but the paralyzing dread dissolved because the fear had fulfilled its biological purpose: **it forced him to prepare thoroughly**.

---

## 5. Think About It (Self-Reflection)

* 💭 **Which fear response do you instinctively lean into under pressure:** freeze, run, or fight?
* 💭 **What is something you have been avoiding lately?** What is that avoidance protecting you from, and what is it costing you?
* 💭 **Who is your “Gopi”**—the supportive friend you can honestly confide in when you feel overwhelmed?
"""

# --- TUTORIAL 3: Understanding Anger ---
def format_tut_3(text):
    return """## 1. What is it?

**Anger is a boundary signal.** It warns us that a boundary has been violated, that an injustice has occurred, or that someone we love is being harmed.

Its essential message is:
> ⚡ **Core Message:** _“This is unfair. Something needs to change.”_

For our ancestors, anger supplied the surge of strength needed to repel physical threats to the family or tribe. In modern life, anger arises when we feel disrespected, treated unfairly, betrayed, or blocked from an important goal.

### Anger as an Emotional Mask
Anger rarely travels alone. In the tutorial, **Anjali’s** explosive anger at **Meera** did not come out of nowhere. Beneath her fierce irritation were weeks of quiet sadness, feelings of abandonment, and fear of being left behind.
* **Anger is often the emotion we display publicly**, because it feels strong and protective.
* **Hurt, grief, and fear are the emotions we conceal**, because they make us feel vulnerable.
* Whenever intense anger surges, ask yourself: _“What softer feeling is hiding under this armor?”_

---

## 2. Bodily Signatures of Anger

Anger announces itself in physical sensations long before the intellect processes the situation:
* 💓 Rapid pulse and elevated blood pressure
* 🩸 Flushed or hot face
* 🦷 Clenched jaw and tightened throat
* ✊ Balling hands into fists

### The Myth of “Venting”
Many believe the healthy antidote to anger is **catharsis**—shouting, slamming doors, or punching pillows to “get it out of your system”. Decades of scientific inquiry show the opposite: **venting acts like gasoline on a fire**.

### 🛑 The 4-Step Anger Pause Protocol

| Step | Action | Focus & Technique |
| :--- | :--- | :--- |
| 🧘 **Step 1** | **Pause & Breathe** | Take 10 slow diaphragmatic breaths to settle blood pressure and heart rate. |
| 🔍 **Step 2** | **Look Underneath** | Ask: _“What softer feeling is under this armor?”_ Is it hurt, fear, disrespect, or loss? |
| 🦅 **Step 3** | **Take a Bird’s-Eye View** | Step back and observe the conflict as an objective, neutral third-party witness. |
| 🗣️ **Step 4** | **Speak to the Hurt** | Use _“I felt overlooked”_ (assertive feedback) rather than _“You are selfish”_ (attack). |

---

## 3. What Does Research Say?

#### A. Venting amplifies aggression rather than releasing it
In a definitive 2002 experiment by **Brad Bushman at Iowa State University**, 600 students were provoked into intense anger by harsh feedback on their essays:
* Group 1 punched a heavy bag while thinking about the person who insulted them.
* Group 2 punched the bag while thinking about general physical fitness.
* Group 3 sat quietly in an armchair for two minutes.
* **The results:** Group 1 remained by far the angriest and engaged in the most aggressive retaliation. Sitting quietly in silence allowed the autonomic nervous system to de-escalate.

#### B. The “Fly-on-the-Wall” perspective cools emotional heat
Psychologists **Özlem Ayduk and Ethan Kross** studied people recalling painful interpersonal conflicts:
* Those who relived the incident through their own eyes experienced immediate spikes in blood pressure and renewed distress.
* Those instructed to view the scene from a distance—as if they were a **fly on the wall** watching two humans interact—showed significantly lower cardiovascular reactivity, articulated clearer solutions, and achieved emotional closure.

#### C. The Bodily Map of Emotions
In a 2014 study published in *PNAS* by **Lauri Nummenmaa and colleagues** (701 participants across Finland, Sweden, and Taiwan):
* Participants mapped physical sensations across emotional states.
* **Anger** concentrated intensely in the upper chest, neck, head, and hands—priming the upper body for physical defense.
* **Happiness** illuminated the entire anatomy with energetic sensation.
* **Sadness** decreased activation in the limbs while concentrating heaviness in the throat and chest.

| Emotion | Physical Activation Zones | Deactivation Zones |
| :--- | :--- | :--- |
| 😠 **Anger** | Head, neck, chest, fists | Lower extremities |
| 😊 **Happiness** | Whole body activation | None |
| 😢 **Sadness** | Throat, central chest | Arms and legs |

---

## 4. Case Study: An Everyday Example

**Lakshmi** is a customer support specialist in Chennai. During a team meeting, her manager presents an innovative framework to reduce customer wait times by 40%. The framework was Lakshmi’s—she shared the documentation with him over coffee three days prior. He accepts all accolades without crediting her:
* 🧠 **Thoughts:** _“He stole my work. No one here will ever appreciate me.”_
* 💓 **Body:** Scalp and face burning hot, jaw locked, fingernails digging into her palm.
* 🏷️ **Feelings:** Fierce indignation masking a deeper terror that her career is stalling.

**The Turning Point:**
She drafts an accusatory email accusing him of plagiarism. Before hitting Send, she notices her trembling hands. Remembering the 4-step model:
1. She steps outside for a 10-minute walk around the building.
2. She identifies her core objective: **she wants visibility for her contributions, not a war**.
3. Next morning, she schedules a private 1-on-1 and says: _“I was glad the wait-time framework was received so enthusiastically yesterday. Because I formulated the operational mechanics, I felt overlooked when my name wasn’t included. I’d like to lead the implementation rollout next week.”_

Her manager immediately apologized and assigned her to present the rollout to senior leadership. Her anger was a legitimate boundary alarm—and channeling it constructively achieved the exact justice she sought.

---

## 5. Think About It (Self-Reflection)

* 💭 **What are your personal physiological early-warning signals** that anger is mounting?
* 💭 **Think of a recent argument:** What softer feeling (exhaustion, rejection, insecurity) was hiding underneath your anger?
* 💭 **Do you tend to bottle anger or blow up?** What has that pattern cost your closest relationships?
"""

# --- TUTORIAL 4: Understanding Sadness ---
def format_tut_4(text):
    return """## 1. What is it?

**Sadness is an emotion of pause and connection.** We feel sadness when we lose something or someone precious, or when a deeply held expectation is shattered.

Its biological message is:
> 🌧️ **Core Message:** _“Something important is missing. Slow down, and reach out.”_

While fear and anger rev up the engine for fight-or-flight, sadness deliberately pumps the brakes. For early humans, grief and loss drew members of the tribe together to share burdens and provide protection.

### The Purpose of Slowing Down
When sadness arrives, energy drops, appetite decreases, speech softens, and we crave quiet reflection. This low-energy state serves a vital psychological function:
* It forces the mind to **process and integrate a significant change in reality**.
* It prevents us from recklessly expending energy on goals that are no longer viable.
* Physical tears and quiet withdrawal serve as **unconscious social signals** inviting empathy and care from our community.

---

## 2. Comparing Fear, Anger, and Sadness

| Emotion | Energy State | Evolutionary Message | Adaptive Response |
| :--- | :--- | :--- | :--- |
| ⚡ **Fear** | High Arousal (Fast) | _“Danger is ahead. Get ready.”_ | Prepare, practice, take small steps |
| 🔥 **Anger** | High Arousal (Fast) | _“A boundary was crossed. Act.”_ | Pause, look underneath, address injustice calmly |
| 🌧️ **Sadness** | Low Arousal (Slow) | _“Something was lost. Reconnect.”_ | Rest, reflect, reach out to trusted allies |

> ⚠️ **Healthy Sadness vs. Depression:**
> Sadness is a normal, fluctuating response to loss that gradually eases as we process reality and receive support. **Clinical depression** is a medical condition where profound numbness, hopelessness, and loss of interest persist every day for two weeks or longer. If sadness feels inescapable and paralyzes daily functioning, speaking with a certified counselor or physician is essential.

---

## 3. What Does Research Say?

#### A. Mild sadness sharpens cognitive processing
**Dr. Joseph Forgas at the University of New South Wales** conducted decades of research demonstrating the cognitive upside of temporary mild sadness:
* Individuals in a mildly somber mood demonstrated **higher recall accuracy**, were significantly less susceptible to misleading rumors, and exhibited less bias in decision-making compared to happy peers.
* Happiness encourages broad, heuristic thinking; mild sadness triggers detailed, analytical, and careful scrutiny.

#### B. Social connection is a fundamental biological requirement
In a massive meta-analysis led by **Julianne Holt-Lunstad at Brigham Young University** (synthesizing 148 studies covering over **300,000 individuals**):
* Strong social bonds increased survival rates by **50%** across study periods.
* Chronic social disconnection carried health risks comparable to smoking 15 cigarettes a day—exceeding the risks of physical inactivity and obesity.
* Reaching out when sad is not self-indulgence; it is a life-preserving biological impulse.

---

## 4. Case Study: An Everyday Example

**Neha’s** elder sister **Pooja** married in December and relocated to Nagpur. The sisters had shared a bedroom, daily routines, and every private secret for twenty years:
* 🧠 **Thoughts:** _“The room is so desolate. She has a whole new family now; she won’t have time for me.”_
* 💓 **Body:** Heaviness in the limbs, loss of appetite, spending evenings lying silently in the dark.
* 🏷️ **Feelings:** Lonely, grieved, and ashamed for feeling miserable while the rest of the household celebrated.

**The Turning Point:**
For two weeks, Neha swallowed her sorrow and replied _“I’m fine, Amma”_ to every inquiry. One evening, she sent a brief message to Pooja: _“The room feels so empty without you. I miss you terribly.”_

Pooja dialed immediately, breaking into tears and confessing how homesick she felt in her new environment. They agreed on a standing video call every Sunday evening. Neha then confides in her mother, who holds her and acknowledges her own grief. The emptiness did not evaporate overnight, but the isolation did—because **sadness fulfilled its purpose: it compelled her to reconnect**.

---

## 5. Think About It (Self-Reflection)

* 💭 **When sadness visits, do you tend to isolate or reach out?** What makes reaching out feel difficult?
* 💭 **Recall an instance where a friend noticed your silent sadness.** What specific gesture made you feel seen without feeling judged?
* 💭 **Who in your immediate circle might be carrying silent grief right now** like Raja in the hostel dining hall?
"""

# --- TUTORIAL 5: Understanding Happiness ---
def format_tut_5(text):
    return """## 1. What is it?

**Happiness is a reinforcement signal.** It tells us that an experience or action is beneficial to our well-being and social bonds.

Its biological message is:
> ☀️ **Core Message:** _“This is good. Do it again, and share it.”_

For early human bands, joy after a communal hunt or gathering fruit reinforced habits that kept the group alive. More importantly, celebrating shared success forged deep tribal loyalty. Happiness spreads naturally: in the tutorial, **Sneha’s** achievement sparked genuine joy across her peers, parents, and professors.

---

## 2. Two Distinct Kinds of Happiness

Psychologists and philosophers draw a critical distinction between two experiences of well-being:

| Dimension | 🍦 Short-Term Pleasure (*Hedonia*) | 🌳 Deep, Lasting Well-Being (*Eudaimonia*) |
| :--- | :--- | :--- |
| **Examples** | Eating pastries, buying gadgets, watching reels, likes on Instagram | Nurturing close relationships, mastering a craft, serving community |
| **Duration** | Spikes instantly; vanishes rapidly | Cultivates slowly; sustains over years |
| **Psychological Dynamic** | **Hedonic Adaptation:** We quickly habituate and crave a bigger dose | Provides profound meaning and the sense that life is deeply worthwhile |

> 💡 **The Hedonic Treadmill:**
> Many believe that securing a high salary, buying a vehicle, or winning an award will make them happy permanently. These achievements deliver a real spark of pleasure, but baseline satisfaction soon returns. Lasting fulfillment is built on three steady pillars: **Relationships, Contribution, and Gratitude**.

---

## 3. What Does Research Say?

#### A. Relationships are the single greatest predictor of health
The **Harvard Study of Adult Development**—one of the longest longitudinal studies in human history, tracking participants for over **85 years** under director **Dr. Robert Waldinger**:
* Revealed that neither wealth, cholesterol levels, nor professional prestige predicted longevity.
* **The clearest finding:** People who enjoyed warm, dependable relationships lived longer, stayed physically healthier, and preserved sharper brain function into their 80s and 90s.

#### B. Deliberate gratitude rewires subjective outlook
In a landmark 2003 experiment by **Robert Emmons and Michael McCullough**:
* Students were split into three groups journaling weekly: one listed **blessings**, one listed **hassles/frustrations**, and one listed **neutral daily occurrences**.
* After 10 weeks, the gratitude group rated their lives significantly more optimistically, experienced fewer physical ailments, slept better, and exercised **1.5 hours more per week** than the hassles group.

---

## 4. Case Study: An Everyday Example

**Ayesha** works demanding night shifts at a hospital in Hyderabad. For over a year, she fantasized about purchasing a personal scooter so she would no longer wait for late-night autos in the rain. When she finally purchased the vehicle, she felt ecstatic:
* For two weeks, every journey felt exhilarating.
* By month two, the novelty vanished. The scooter became merely a machine to reach work, and she began fantasizing about expensive jewelry to regain that missing excitement.
* 🧠 **Thoughts:** _“I got what I wanted. Why do I feel so uninspired again?”_
* 💓 **Body:** Lethargy and exhaustion on days off.
* 🏷️ **Feelings:** Flat, restless, disengaged.

**The Turning Point:**
A senior nurse suggested writing down three specific things she appreciated before sleeping. Within a week, Ayesha began noticing quiet bright spots during her shifts: an elderly patient’s recovery, a colleague bringing her homemade chai, the cool evening breeze on her commute.

On Sunday, she used her scooter to take her grandmother to the temple and enjoy dosas together. Her grandmother spoke of the outing for weeks. Ayesha realized: **the machine did not generate happiness—using it to enrich relationships did**.

---

## 5. Think About It (Self-Reflection)

* 💭 **Think of a possession you were convinced would make you happy.** How long did the excitement actually last before returning to baseline?
* 💭 **When did you last experience genuine joy purely from helping someone else?**
* 💭 **Who are the rare friends whose good fortune makes you feel completely happy without an ounce of jealousy?**
"""

print("Defined formatters for tutorials 1-5")

# --- TUTORIAL 6: Understanding Guilt ---
def format_tut_6(text):
    return """## 1. What is it?

**Guilt is a moral repair signal.** We feel guilt when we have committed an action that violates our internal values, breaks trust, or inflicts harm on another person.

Its biological and social message is:
> ⚖️ **Core Message:** _“Something I did was wrong. It needs repair.”_

In ancestral hunter-gatherer bands, deception, hoarding food, or abandoning duties threatened the entire tribe. Guilt evolved as an inner alarm system prompting individuals to confess, make amends, and restore community trust.

---

## 2. Guilt vs. Shame vs. Toxic Self-Blame

Understanding the distinction between healthy guilt and destructive shame is essential:

| Dimension | ⚖️ Healthy Guilt | 🪞 Destructive Shame | 🔄 Toxic Self-Blame |
| :--- | :--- | :--- | :--- |
| **Cognitive Focus** | Focuses on the **behavior**: _“I did something bad.”_ | Focuses on the **identity**: _“I am a bad person.”_ | Obsessively replaying mistakes without acting |
| **Emotional Response** | Discomfort that pushes toward restitution | Humiliation that causes one to hide and withdraw | Paralysis, chronic insomnia, self-loathing |
| **Outcome** | Restores relationships and clears conscience | Isolates and damages self-worth | Exhausts emotional energy without helping anyone |

### How to Make Genuine Amends
A superficial “sorry” rarely heals a broken bond. A real apology includes four deliberate components:
1. 🎯 **Name the specific action:** State plainly what you did without defensive excuses.
2. 🫂 **Acknowledge the emotional impact:** Validate how your action affected the other person.
3. 🛠️ **Offer restitution:** Ask: _“How can I make this right?”_ and take concrete remedial action.
4. 🛡️ **Commit to changed behavior:** Ensure the mistake is not repeated.

---

## 3. What Does Research Say?

#### A. The essential components of an effective apology
In a 2016 study by **Roy Lewicki and colleagues at Ohio State University** (755 participants evaluating apologies across professional and personal breaches):
* Researchers identified six apology elements.
* **The single most important factor:** Explicitly **accepting responsibility** for one's actions.
* The second most important was an **offer of repair**.
* Merely expressing regret without taking responsibility scored lowest in restoring trust.

#### B. Guilt repairs; shame destroys
Psychologist **June Tangney at George Mason University** spent three decades researching guilt versus shame:
* Individuals prone to **guilt** demonstrated higher empathy, engaged in constructive conflict resolution, and maintained stronger relationships.
* Individuals prone to **shame** frequently externalized blame, responded with defensiveness and hostility, and suffered higher rates of anxiety and depression.

---

## 4. Case Study: An Everyday Example

**Ravi** is a marketing coordinator at a media agency in Mumbai. He promised to cover his coworker **Meenakshi’s** weekend shift so she could attend her sister’s wedding in Jaipur. On Saturday morning, Ravi slept through his alarm, forgot the shift, and did not arrive. Meenakshi was forced to cancel her travel plans:
* 🧠 **Thoughts:** _“I ruined her sister’s wedding. She will hate me forever. I’m a terrible friend.”_
* 💓 **Body:** Hollow stomach, chest heaviness, inability to concentrate or sleep.
* 🏷️ **Feelings:** Intensely guilty and tempted to call in sick on Monday to avoid facing her.

**The Turning Point:**
Ravi realized that avoiding her was shame—it would leave the wound festering. He decided to use his guilt constructively:
1. He arrived early Monday and asked Meenakshi to speak in private.
2. He did not offer excuses: _“Meenakshi, I broke my promise and caused you to miss your sister’s wedding. No excuse makes that acceptable. I am deeply sorry for letting you down.”_
3. He volunteered to cover her next three holiday shifts and arranged an artisan gift hamper for the newlyweds with a handwritten note.

Meenakshi was initially hurt, but seeing Ravi take unconditional responsibility allowed her to forgive him. His guilt had served its evolutionary purpose: **it forced him to make amends and preserve the partnership**.

---

## 5. Think About It (Self-Reflection)

* 💭 **When you make a mistake, do you tend to feel guilt (focusing on what you did) or shame (focusing on who you are)?**
* 💭 **What is a genuine apology you owe someone?** What has prevented you from delivering it?
* 💭 **Are you currently carrying chronic self-blame over an old mistake?** What would it look like to finally forgive yourself and move forward?
"""

# --- TUTORIAL 7: Jealousy and Admiration ---
def format_tut_7(text):
    return """## 1. What is it?

**Jealousy and admiration are two divergent reactions to the exact same stimulus:** witnessing someone who possesses a quality, achievement, or resource that we deeply desire.

Both begin with a social comparison. The fundamental difference lies in **where the emotional energy flows**:
* 🔄 **Jealousy turns energy inward:** _“Why them and not me?”_ (breeds resentment and self-pity).
* 🚀 **Admiration turns energy forward:** _“How did they achieve that, and what can I learn?”_ (fuels inspiration and effort).

> 💡 **Core Message:**
> Jealousy is rarely about the other person; it is a mirror reflecting **what you secretly care about**. Listened to skillfully, jealousy reveals dormant ambitions. Ignored, it breeds toxic bitterness.

---

## 2. Deciding How to Channel Jealousy

When jealousy surges, asking yourself one strategic question changes everything:

| Reflective Question | If the Answer Is... | What the Emotion Is Asking You to Do |
| :--- | :--- | :--- |
| **Can I work toward this through practice and effort?** | ✅ **Yes** (skills, grades, fitness, public speaking) | **Convert it into Admiration:** Study their daily habits, ask for their advice, and commit to the deliberate practice required. |
| **Is this outside my control?** | ❌ **No** (family wealth, genetics, height, past background) | **Identify the Underlying Emotional Need:** Jealousy is pointing to a longing for belonging, respect, or security. Find a healthy, authentic way to satisfy that need. |

### Looking Behind the Curtain of Success
Jealousy thrives when we observe only the polished outcome and ignore the invisible labor. In the tutorial, **Rohit’s** bitter jealousy over **Vikram’s** conference selection evaporated when he witnessed Vikram in the laboratory at midnight—exhausted, anxious, and meticulously rebuilding his slide deck for the fifth time. Seeing the effort humanized the achievement.

---

## 3. What Does Research Say?

#### A. Benign envy vs. Malicious envy
In foundational research by **Niels van de Ven and colleagues at Tilburg University**:
* **Benign envy (Admiration):** Involves positive appraisal of the other person's accomplishment, leading individuals to study longer, set higher academic goals, and improve their own performance.
* **Malicious envy:** Involves resentment and schadenfreude (hoping the other person stumbles), which drains motivation and degrades subjective well-being.

#### B. Social comparison on digital platforms
Psychologist **Ethan Kross and colleagues at the University of Michigan** tracked emotional well-being relative to smartphone usage:
* Passive social media scrolling directly correlated with spikes in envy and decreases in life satisfaction.
* Why? Digital feeds curate the top 1% of celebratory highlights, creating a false illusion that everyone else is effortlessly successful.

---

## 4. Case Study: An Everyday Example

**Rohit** and **Vikram** are final-year computer science researchers in Pune. When Vikram is selected to present his paper at an international symposium in Singapore, Rohit is consumed with bitterness:
* 🧠 **Thoughts:** _“The professors favor him. His paper wasn’t even that original. Why does he get all the breaks?”_
* 💓 **Body:** Tight chest, acid reflux, avoiding common lab rooms.
* 🏷️ **Feelings:** Insecure, envious, and ashamed of his own spite.

**The Turning Point:**
Rohit stopped replying to Vikram’s messages. Two weeks later, Rohit forgot his notebook in the lab and returned at 11:30 PM. He found Vikram sitting alone under fluorescent lights, red-eyed and trembling with anxiety over presentation slides.

Rohit realized Vikram was not a spoiled rival; he was a terrified student working himself to exhaustion. Rohit offered to rehearse the Q&A section with him. Over the next week:
* Rohit learned how Vikram structured literature citations.
* Vikram shared his data-cleaning scripts.
* By turning **jealousy into admiration**, Rohit unlocked the very knowledge he needed to publish his own paper the following semester.

---

## 5. Think About It (Self-Reflection)

* 💭 **Who is someone whose recent success provoked a pang of jealousy in you?** What does that jealousy reveal about your own unfulfilled goals?
* 💭 **Look behind their accomplishment:** What invisible sacrifices, rejections, or hours of unglamorous practice made their success possible?
* 💭 **How could you reach out to them with genuine admiration this week?**
"""

# --- TUTORIAL 8: Reality and Interpretations ---
def format_tut_8(text):
    return """## 1. What is it?

In Module 1, you discovered that emotions are signals. Module 2 explores a deeper inquiry: **Where do those signals actually originate?**

The foundation begins by distinguishing between two fundamentally different concepts:
* 📏 **Reality:** Anything that can be measured, verified, videotaped, or tested. Reality is objective fact.
* 👓 **Interpretation:** The story, meaning, or narrative our brain constructs about that reality. Interpretation is subjective and holds no objective truth.

### 🔄 The Cognitive Chain

| Stage | What Happens | Concrete Example |
| :--- | :--- | :--- |
| 📏 **1. Reality** | The objective, verifiable fact | _“The bus departed 5 minutes before I arrived at the stop.”_ |
| 👓 **2. Interpretation** | The subjective story our brain creates | _“The universe is deliberately working against me.”_ |
| 💥 **3. Emotion** | The physiological feeling produced by the story | Fierce frustration, agitation, and helplessness. |

> 💡 **The Great Insight:**
> Events do not cause our feelings directly. **Our interpretations of events cause our feelings.** Change the interpretation, and the emotional response shifts naturally.

---

## 2. Reality vs. Interpretation: Spotting the Difference

| Statement | Reality (Fact) | Interpretation (Story) | Why It Matters |
| :--- | :--- | :--- | :--- |
| _“The bus arrived at 8:45 AM.”_ | ✅ Yes | ❌ No | Can be verified with a clock. |
| _“The bus driver is completely incompetent.”_ | ❌ No | ✅ Yes | An opinion; cannot be measured in a lab. |
| _“She did not reply to my text for 6 hours.”_ | ✅ Yes | ❌ No | Verifiable timestamp on a smartphone. |
| _“She doesn’t care about our friendship anymore.”_ | ❌ No | ✅ Yes | A speculative story that breeds anxiety. |
| _“I scored 42 out of 100 on the exam.”_ | ✅ Yes | ❌ No | Objective score on paper. |
| _“I am hopeless at mathematics.”_ | ❌ No | ✅ Yes | A fixed identity label that closes off growth. |

---

## 3. What Does Research Say?

#### A. The ABC Model of Cognitive Psychology
Pioneered by **Dr. Albert Ellis and Dr. Aaron Beck** (the fathers of Cognitive Behavioral Therapy):
* **A (Activating Event):** An external occurrence in reality.
* **B (Belief / Interpretation):** What you tell yourself about the event.
* **C (Consequence / Emotion):** How you feel and behave.
* Most people mistakenly believe that **A causes C**. Modern neuroscience confirms that **B is the master driver**.

#### B. Confirmation Bias and Narrative Construction
In **Nobel Laureate Daniel Kahneman’s** work (*Thinking, Fast and Slow*):
* The brain operates on a cognitive rule: **WYSIATI** (_“What You See Is All There Is”_).
* When a gap in information exists, the brain's intuitive System 1 instantly invents a coherent story, regardless of whether evidence exists.
* Learning to pause and ask: _“What is fact, and what is story?”_ activates the rational prefrontal cortex.

---

## 4. Case Study: An Everyday Example

**Anuj** shares an apartment with **Kartik** in Bengaluru. On Friday evening, Anuj returns home from a grueling 10-hour shift. In the kitchen sink, Kartik’s breakfast bowl and tea mug are sitting unwashed:
* 📏 **Reality:** A ceramic bowl and mug with tea residue are in the sink basin.
* 👓 **Anuj’s Interpretation:** _“Kartik expects me to be his maid. He has zero respect for my time or shared boundaries.”_
* 💓 **Body & Emotion:** Blood pressure spikes, jaw clenches, burning rage.

**Testing the Lens:**
Anuj storms toward Kartik’s room ready to yell. Halfway down the corridor, he pauses and forces himself to separate fact from narrative:
* _Fact:_ Two dishes are unwashed.
* _Story:_ He does not respect me.

He knocks calmly: _“Hey Kartik, I noticed your breakfast dishes are in the sink. Can you clear them before cooking dinner?”_
Kartik looks up from his laptop, startled: _“Oh Anuj, I am so sorry! My sister was rushed to the clinic this morning and I sprinted out the door. Cleaning them right now.”_

If Anuj had acted on his **interpretation**, a bitter battle would have erupted. By addressing only **reality**, the issue was resolved in thirty seconds.

---

## 5. Think About It (Self-Reflection)

* 💭 **Think of a recent moment you felt deeply irritated with someone:** What was the measurable reality, and what was the narrative your mind created?
* 💭 **What is a personal assumption you make about yourself** that you treat as fact, but is really just an interpretation?
* 💭 **How would your stress levels change if you consistently waited for evidence before judging intentions?**
"""

# --- TUTORIAL 9: Understanding Beliefs ---
def format_tut_9(text):
    return """## 1. What is it?

If interpretations are the stories we tell in specific moments, **beliefs are the master lenses through which all stories are born**.

A belief is an enduring idea or conviction we hold to be true about ourselves, others, or the world.
* Beliefs operate largely **below conscious awareness**.
* They filter which details we notice, which we ignore, and how we interpret everyday reality.

### 👓 How Beliefs Shape Everyday Reactions

| Level | Component | Experience in Action |
| :--- | :--- | :--- |
| 🧠 **Underlying Belief** | Enduring unconscious filter | _“People are generally untrustworthy and will exploit me.”_ |
| 📏 **Objective Reality** | Observable event | A colleague warmly offers to proofread your report. |
| 💭 **Instant Interpretation** | Narrative constructed by belief | _“They are looking for errors so they can report me to the manager.”_ |
| 🛡️ **Resulting Emotion** | Felt emotional reaction | Suspicion, heightened anxiety, and guarded hostility. |

---

## 2. Effective vs. Ineffective Beliefs

Rather than categorizing beliefs as “true or false” or “right or wrong”, this course asks a pragmatic question: **Is this belief effective?**
* **Effective Belief:** An idea that expands your capacity, encourages effort, builds connection, and produces healthy results.
* **Ineffective Belief:** An idea that constricts your potential, provokes chronic negative emotion, and sabotages relationships.

### The 3 Warning Signs of an Ineffective Belief
How do you know when a long-held belief is no longer serving you? Look for these three signals:

| Warning Signal | What to Notice | Example |
| :--- | :--- | :--- |
| 📉 **1. Unwanted Results** | Repeatedly falling short of goals despite hard work | Procrastinating on applications because you believe you won't get picked |
| 🗣️ **2. Unwanted Feedback** | Multiple independent people offer the exact same constructive criticism | Colleagues saying: _“You don't communicate before decisions”_ |
| 🌧️ **3. Repeated Negative Emotions** | Recurring patterns of resentment, dread, or defensive anger in similar contexts | Feeling panicked whenever authority figures give minor feedback |

---

## 3. What Does Research Say?

#### A. Beliefs distort how we evaluate objective scientific evidence
In a classic 1979 **Stanford University experiment by Charles Lord, Lee Ross, and Mark Lepper**:
* 48 students with opposing views on capital punishment read two carefully balanced scientific studies.
* Proponents judged the pro-death-penalty study as brilliantly designed and dismissed the counter-study.
* Opponents did the exact reverse.
* After reading identical data, **both groups became more polarized**. Their pre-existing beliefs determined how they interpreted the evidence.

#### B. The Stress Mindset Study
In 2013, researchers **Alia Crum, Peter Salovey, and Shawn Achor** studied employees at a major financial institution undergoing layoffs:
* Group 1 watched short videos explaining that stress enhances cognitive performance, accelerates learning, and builds grit (**Stress-is-Enhancing Mindset**).
* Group 2 watched videos highlighting the health hazards of stress (**Stress-is-Debilitating Mindset**).
* Group 1 experienced significant reductions in anxiety, improved work performance, and fewer physical health complaints. **The objective stress was identical; their underlying belief about stress transformed the outcome.**

---

## 4. Case Study: An Everyday Example

**Sunil** grew up observing his father maintain fierce independence. Over decades, it solidified into an unconscious rule: _“A real man solves his own problems. Asking for help is weakness.”_

This belief worked exceptionally well in school, where individual exams rewarded solo study. But when Sunil joined an enterprise software firm in Bengaluru:
* 📉 **Results:** He worked until 11 PM every night attempting to decipher complex codebases alone, repeatedly missing project deadlines.
* 🗣️ **Feedback:** His engineering lead told him: _“Sunil, you wasted three days on a module that our senior developer could have explained in 10 minutes.”_
* 🌧️ **Emotions:** Chronic morning dread, exhaustion, and imposter syndrome.

**The Awakening:**
All three warning signs were glaring. Sunil realized his belief was not “morally wrong”, but it was **deeply ineffective** in an interconnected professional workplace. It was a tool that helped him pass exams, but was now destroying his career and health. Recognizing this was the vital first step toward rewriting it.

---

## 5. Think About It (Self-Reflection)

* 💭 **What is a core belief you absorbed from your upbringing?** Is it still effective for the person you want to become today?
* 💭 **Examine your recent life:** Are you currently experiencing any of the 3 warning signs (unwanted results, repeated feedback, or recurring negative feelings)?
* 💭 **What is an old belief that served you well in school, but is holding you back at college or work?**
"""

# --- TUTORIAL 10: How to Change Beliefs ---
def format_tut_10(text):
    return """## 1. What is it?

In Tutorial 9, you learned how to identify an ineffective belief. **Tutorial 10 provides the blueprint for rewriting it.**

Beliefs are not immutable stone tablets; they are reinforced neural pathways. If a belief was learned through repetition and experience, it can be unlearned and rebuilt through deliberate practice.

In the tutorial, **Tara** held the conviction: _“I am naturally terrible at public speaking.”_ This belief paralyzed her in seminars. Her professor revealed that she too had once broken down and wept on stage, but had acquired mastery through progressive exposure. Tara adopted a new, workable belief:
> 🌱 **The New Belief:** _“With steady practice, I can become an effective communicator.”_

---

## 2. The 6-Step Belief Transformation Framework

| Step | Phase | Core Action |
| :--- | :--- | :--- |
| 🔍 **Step 1** | **Awareness** | Write down the old belief in plain, unfiltered words. |
| ⚖️ **Step 2** | **Examine Evidence** | Ask: _“What concrete facts support this? What facts contradict it?”_ |
| 🎯 **Step 3** | **Believable Reframe** | Replace with a realistic, progressive conviction (not fake toxic positivity). |
| 🪜 **Step 4** | **Daily Micro-Actions** | Execute one tiny, manageable exposure action every single day. |
| 📓 **Step 5** | **Track in Writing** | Maintain an empirical daily log recording real-world wins. |
| 🎉 **Step 6** | **Celebrate & Share** | Validate and anchor small victories with trusted mentors and peers. |

1. 🔍 **Awareness:** Write the old belief in simple, unfiltered language (e.g., _“I can’t speak in public”_).
2. ⚖️ **Examine the Evidence:** Is this belief helping me? What concrete facts support it, and what facts contradict it?
3. 🎯 **Formulate a Believable New Belief:** Avoid unrealistic affirmations like _“I am the greatest speaker in the world.”_ Choose realistic, incremental growth: _“With practice, I can express my ideas clearly.”_
4. 🪜 **Take Daily Micro-Actions:** Tara started by reading a single sentence aloud in her bedroom.
5. 📓 **Track Progress in Writing:** Tara kept a 7-day log (Day 1: one line; Day 4: spoke during group discussion; Day 10: introduced a guest lecturer).
6. 🎉 **Celebrate and Share:** Validate small steps with trusted mentors.

---

## 3. Bandura’s 4 Sources of Self-Efficacy

Why was Tara’s transformation successful? Renowned Stanford psychologist **Albert Bandura** identified four biological pillars that construct our belief in our abilities (**_self-efficacy_**):

| Source of Self-Efficacy | Definition | How It Showed Up in Tara's Journey |
| :--- | :--- | :--- |
| 🏆 **1. Mastery Experiences** | Personal, direct success through gradual effort | Saying 1 sentence, then contributing 2 points, then hosting a seminar |
| 👥 **2. Vicarious Modeling** | Seeing someone with a similar background succeed | Hearing her professor describe crying on stage and learning to speak |
| 🗣️ **3. Social Persuasion** | Encouragement and coaching from people we trust | Her trusted friend saying: _“I believe in you; you prepared well.”_ |
| 💓 **4. Physiological Reinterpretation** | Reading internal bodily sensations constructively | Reinterpreting her racing heart as readiness rather than a signal to flee |

---

## 4. What Does Research Say?

#### A. The tracking effect on behavioral transformation
In a meta-analysis led by **Benjamin Harkin** (synthesizing 138 studies across **20,000 individuals**):
* Consistent progress monitoring dramatically increased goal achievement.
* The effect was doubled when progress was **recorded in writing** and **shared with a supportive ally**.

#### B. The Power of Small Wins
Harvard Business School researchers **Teresa Amabile and Steven Kramer** analyzed 12,000 daily diary entries from 238 knowledge professionals:
* The single most powerful factor boosting daily motivation was **making incremental progress on meaningful work**.
* Minor victories release dopamine, reinforcing the neural belief that effort yields competence.

---

## 5. Case Study: An Everyday Example

In Tutorial 9, **Sunil** realized his belief (_“Asking for help is weakness”_) was sabotaging his career. He formulated a new belief: _“Asking strategic questions allows me to master software faster.”_

He launched a 7-day micro-experiment:
* 📓 **Day 1:** He asked a colleague a single question regarding an IDE shortcut. His face felt hot, but the answer saved him 90 minutes. He wrote: _“Felt awkward. Then immensely relieved.”_
* 📓 **Day 3:** He asked his project manager to review his architecture diagram before writing code. The manager replied: _“Excellent initiative to verify this early.”_
* 📓 **Day 7:** A junior developer asked Sunil for guidance. Sunil realized that mentoring felt rewarding, not weak.

Within 30 days, Sunil was hitting every release deadline. The old belief still occasionally whispered, but **daily recorded micro-actions made the new belief solid reality**.

---

## 6. Think About It (Self-Reflection)

* 💭 **Which of Bandura’s 4 sources has historically had the greatest impact on your self-belief?**
* 💭 **What is a skill you once felt hopeless at, but eventually mastered?** What was the exact sequence that shifted your belief?
* 💭 **Who is the mentor or peer in your life who can act as your “professor”**—someone who has struggled with what you are facing?
"""

# --- TUTORIAL 11: Judgment and Feedback ---
def format_tut_11(text):
    return """## 1. What is it?

In earlier tutorials, you explored reality, interpretation, and underlying beliefs. **Tutorial 11 applies these principles to interpersonal communication.**

> ⚠️ **The Core Definition:**
> **A judgment is a subjective interpretation stated as if it were an objective fact.**

In the tutorial, **Ravi** submitted his software module late, causing the team to lose marks. His teammate **Riya** snapped: _“You are completely irresponsible!”_ Let us dissect the anatomy of that statement:

| Step in Communication | What It Actually Is | The Reality vs. The Story |
| :--- | :--- | :--- |
| **1. Reality** | What took place | Ravi submitted his project module at 6:00 PM instead of 2:00 PM. |
| **2. Riya’s Belief** | Her underlying value | Responsible teammates prioritize group deadlines. |
| **3. Riya’s Interpretation** | Her internal narrative | _“Ravi doesn’t care about our grades.”_ |
| **4. What Riya Said (Judgment)** | Interpretation stated as a fact | _“You are irresponsible.”_ |

---

## 2. Judgment vs. Constructive Feedback

| Dimension | 💥 Judgment | 🌱 Constructive Feedback |
| :--- | :--- | :--- |
| **Pronoun Focus** | Starts with **“You”**: _“You are lazy.”_ | Starts with **“I”**: _“I noticed that...”_ |
| **Target** | Attacks the **person’s entire identity** | Pinpoints a **specific behavior and its impact** |
| **Psychological Impact** | Triggers fight-or-flight; closes dialogue | Invites reflection; keeps dialogue open |
| **Conversational Goal** | Venting frustration; blaming | Solving problems; building collaboration |

### 🛠️ The 3-Part Constructive Feedback Formula

| Part | Component | Script Example |
| :--- | :--- | :--- |
| 📏 **1. Observable Reality** | State what occurred without editorializing or character attacks | _“I noticed that the group project draft was submitted two hours after our agreed deadline.”_ |
| 💥 **2. Impact & Emotion** | Describe the concrete consequence and how it affected you | _“Because of the delay, our team lost marks for punctuality, and I felt stressed and anxious.”_ |
| 🤝 **3. Future Request** | State an actionable, collaborative request for next time | _“Next time, could you please message the group at least 4 hours in advance if you anticipate a delay?”_ |

---

## 3. What Does Research Say?

#### A. The Defensiveness Cascade in Conflict
In four decades of couples and team research by **Dr. John Gottman**:
* Criticism (attacking personality or character) was identified as the single greatest predictor of relationship dissolution.
* In contrast, stating a specific complaint regarding an outcome preserved partnership trust.

#### B. The 5:1 Psychological Ratio
Gottman’s research demonstrated that maintaining collaboration requires at least **5 positive interactions for every 1 critical interaction**. When feedback feels like an attack on identity, psychological safety collapses.

---

## 4. Case Study: An Everyday Example

**Priya** leads a college design committee in Pune. Her peer **Kunal** missed two consecutive subcommittee planning sessions:
* 💥 **The Judgment Path:** Priya wants to text: _“You are completely unreliable and selfish.”_
  * _Result:_ Kunal becomes defensive, stops attending completely, and badmouths Priya to friends.
* 🌱 **The Feedback Path:** Priya pauses, separates reality from story, and speaks to him in the canteen:
  * _“Kunal, I noticed you weren’t able to attend the last two design meetings. Because your input on branding was missing, the timeline got delayed and I felt stressed trying to coordinate alone. Is everything alright, and can we count on you for Friday?”_
  * _Result:_ Kunal apologizes, explains that his father was admitted to the hospital, and commits to reviewing the digital assets from home.

---

## 5. Think About It (Self-Reflection)

* 💭 **Think of a time someone passed a harsh judgment on you:** How did your body and mind react?
* 💭 **What is a recurring judgment you make about a friend or family member?** How could you restate it as a behavior and an emotional impact?
* 💭 **Rewrite this sentence as clean feedback:** _“You never listen to anyone.”_
"""

print("Defined formatters for tutorials 6-11")

# --- TUTORIAL 12: Empathy ---
def format_tut_12(text):
    return """## 1. What is it?

**Empathy is understanding another person's experience from their unique vantage point.**

The fundamental principle of empathy is captured in a simple truth:
> 🤝 **Core Principle:** _“Everyone has a story you know nothing about.”_

In the tutorial, **Rani** submitted her portion of the group project late. Her teammates reacted with completely different lenses:
* **Rahul** snapped: _“She is irresponsible. We can never rely on her.”_
* **Priya** paused: _“Maybe she is facing an emergency. Let us ask if she needs help before we judge.”_

When Rani later explained that her mother had been rushed to the hospital, Rahul’s anger vanished and he offered support. The reality did not change—**their awareness of the story changed**.

---

## 2. Same Reality, Different Lenses

| Dimension | 💥 Rahul’s Lens | 🫂 Priya’s Lens |
| :--- | :--- | :--- |
| **Observable Reality** | Rani submitted the project module 4 hours late | Rani submitted the project module 4 hours late |
| **Underlying Belief** | _“Being punctual is the only true sign of respect.”_ | _“People encounter unforeseen personal crises.”_ |
| **Interpretation** | _“She doesn’t care about our grades.”_ | _“She might be going through something difficult.”_ |
| **Resulting Emotion** | 😠 Resentment and anger | 🤝 Concern and empathy |

### What Empathy Is Not
* ❌ **Empathy is not total agreement:** Understanding why someone acted does not mean endorsing the action or excusing the consequences.
* ❌ **Empathy does not mean having no boundaries:** You can hold deep empathy for someone while still establishing clear expectations and protecting your own mental health.

---

## 3. What Does Research Say?

#### A. The Neurobiology of Empathy vs. Compassion
Groundbreaking neuroimaging research by **Dr. Tania Singer at the Max Planck Institute**:
* **Empathy** activates the pain matrix in the brain (sharing the distress of another).
* When empathy is prolonged without action, it can lead to emotional exhaustion.
* **Compassion**, by contrast, activates neural networks associated with warmth, care, and proactive helping—protecting against burnout while fostering resilience.

#### B. The Illusion of Insight
Psychologist **Nicholas Epley at the University of Chicago** demonstrated that most people overestimate how accurately they can guess what others think:
* Simply asking curious, open questions (*perspective-getting*) was **significantly more effective** than merely imagining another person's thoughts (*perspective-taking*).

---

## 4. Case Study: An Everyday Example

**Sameer** works as a software trainee in Pune. His team lead **Vikram** has been curt and critical all week, rejecting pull requests with terse one-line comments:
* 🧠 **Thoughts:** _“Vikram is arrogant. He hates me and wants me off the team.”_
* 💓 **Body:** Knot in the stomach, avoidance of team lunches.
* 🏷️ **Feelings:** Anxious, defensive, resentful.

**The Empathy Pause:**
Sameer remembers the principle: _“Everyone has a story.”_ He asks a senior colleague over tea: _“Is Vikram usually this abrupt?”_
The colleague whispers: _“His father was diagnosed with late-stage cancer last Friday. He is working 12 hours a day while coordinating hospital treatments.”_

Sameer’s resentment instantly transformed into deep understanding. When Vikram left another blunt comment, Sameer replied: _“Understood, Vikram. Refactoring the code as requested. Also, please let me know if there are documentation tasks I can take off your plate this week.”_
Vikram called him five minutes later to express gratitude. **Empathy dismantled an escalating conflict before it ever began.**

---

## 5. Think About It (Self-Reflection)

* 💭 **What is the difference between having empathy for someone and excusing their behavior?**
* 💭 **Think of a person who recently irritated you:** What might their invisible story or pressure be right now?
* 💭 **How can asking “What might their story be?” change how your body responds to interpersonal frustration?**
"""

# --- TUTORIAL 13: How the Brain Learns New Things ---
def format_tut_13(text):
    return """## 1. What is it?

For decades, popular culture claimed that adult brains are fixed and unchangeable. **Modern neuroscience proves the exact opposite: your brain is dynamically plastic.**

> 🧠 **Neuroplasticity:**
> The physical ability of the brain to rewire, grow new synaptic connections, and adapt throughout life in response to deliberate practice and learning.

In the tutorial, students drew a bird with their dominant hand, and then repeated the exercise with their **non-dominant hand**.
* Initially, using the non-dominant hand felt clumsy, awkward, and frustrating.
* **That awkwardness is not incompetence:** it is the physical sensation of dormant neural pathways being activated for the first time!

---

## 2. How Neurons Form Pathways

### 🛣️ The 3 Stages of Neural Pathway Formation

| Stage | Biological Process | The Experience |
| :--- | :--- | :--- |
| 🌿 **1. First Attempt** | Initial synaptic connection | Faint, narrow jungle trail. Feels awkward, slow, and clumsy. |
| 🔧 **2. Repeated Practice** | Pathway cleared, myelin insulation added | The trail widens into a dirt road. Actions require less conscious strain. |
| 🚀 **3. Mastery** | Thick myelin sheaths wrap axons | High-speed neural superhighway. Signals transmit up to **100× faster** effortlessly. |

* **Neurons that fire together, wire together.**
* When you struggle with a new concept (a foreign language, differential calculus, coding), your brain wraps axons in **myelin**—an insulating sheath that accelerates neural signal transmission by up to **100 times**.
* **Struggle is not a sign of failure; struggle is the biological catalyst for growth.**

---

## 3. What Does Research Say?

#### A. The London Taxi Driver Brain Scans
In a famous study by **Dr. Eleanor Maguire at University College London**:
* London cab drivers spend 3–4 years memorizing 25,000 streets and 100,000 landmarks (“The Knowledge”).
* MRI scans revealed that taxi drivers possessed significantly larger **posterior hippocampi** (the brain region governing spatial navigation) compared to control groups.
* The physical brain tissue expanded in direct proportion to the years spent navigating the streets.

#### B. The Neural Signature of Effort
Stanford psychologist **Dr. Carol Dweck and neuroscientists**:
* Tracked student brain waves during challenging academic problem-solving.
* Students who understood that effort expands neural density showed far higher brain activity during errors and mastered difficult concepts significantly faster than peers who believed talent was innate.

---

## 4. Case Study: An Everyday Example

**Rahul** enrolled in an introductory Python programming course. For the first two weeks, understanding nested loops and recursion felt like hitting a brick wall:
* 🧠 **Thoughts:** _“My brain isn’t wired for logic. Only math geniuses can code.”_
* 💓 **Body:** Headache, eye strain, feeling sleepy whenever he opened his laptop.
* 🏷️ **Feelings:** Defeated and on the verge of dropping the elective.

**The Shift:**
Rahul remembered the bird-drawing exercise. He realized his brain was currently at the awkward “non-dominant hand” stage. Instead of studying in marathon 6-hour binges, he committed to **25 minutes of coding every single morning**:
* Week 3: Syntax errors became easier to troubleshoot.
* Week 5: He built his first automated text game without consulting solutions.
* His intelligence had not magically changed—**his neural circuitry had physically wired the pathways**.

---

## 5. Think About It (Self-Reflection)

* 💭 **Why does learning something entirely new feel physically uncomfortable?**
* 💭 **Recall a skill you found baffling at first (cycling, swimming, playing guitar):** What did it feel like when the neural connections finally clicked?
* 💭 **How would your daily study habits transform if you viewed confusion as neural growth in real time?**
"""

# --- TUTORIAL 14: The Magic of Failures ---
def format_tut_14(text):
    return """## 1. What is it?

In Tutorial 13, you learned that the brain grows through struggle. **Tutorial 14 takes this principle one step further: even outright failure is premium fuel for the brain.**

Most people treat failure as an absolute verdict:
* ❌ _“I failed this test, therefore I am a failure.”_
* 🌱 **The Growth Mindset alternative:** _“I failed this test, which means my current strategy was incomplete.”_

> 💡 **Core Insight:**
> Failure is not an identity; **failure is diagnostic data**. It pinpoints the precise boundaries of your current knowledge so you can adjust your strategy.

---

## 2. The 3-Step Failure Debrief Protocol

When a project, exam, or interview collapses, do not retreat into shame. Conduct a clean post-mortem using three objective questions:

| Debrief Step | Reflective Question | Example |
| :--- | :--- | :--- |
| 🌟 **1. What Went Well?** | What parts of my preparation or performance were solid? | _“I delivered the opening three slides with clarity and confidence.”_ |
| 🔍 **2. What Went Wrong?** | Where did the breakdown occur factually? | _“I ran out of time on slide 8 because I didn't rehearse with a timer.”_ |
| 🎯 **3. What Will I Adjust?** | What is one concrete systemic change for next time? | _“I will conduct two full dry-runs with a stopwatch before the next presentation.”_ |

---

## 3. What Does Research Say?

#### A. Brain electrical activity during mistakes (ERN Waves)
In neuroscientific research by **Dr. Jason Moser at Michigan State University**:
* Researchers recorded EEG brain waves (**Error-Related Negativity, or ERN**) when participants made errors on tests.
* Individuals with a **growth mindset** showed large ERN spikes, indicating their brains actively engaged with the error, analyzed the discrepancy, and modified future behavior.
* Individuals with a **fixed mindset** showed muted brain signals—their brains literally avoided looking at the mistake to protect self-esteem.

#### B. Normalizing failure accelerates innovation
Harvard Business School professor **Dr. Amy Edmondson**’s research on psychological safety revealed that elite medical teams and engineering teams did not make fewer mistakes—**they spoke about mistakes openly without fear of punishment**, allowing the entire organization to iterate and learn faster.

---

## 4. Case Study: An Everyday Example

**Ananya** auditioned for the college debating team. She prepared for five days, but during the live rebuttal, her train of thought fractured, she stumbled over definitions, and she was eliminated in the first round:
* 🧠 **Thoughts:** _“I humiliated myself. Everyone was laughing at me. I'm never doing public speaking again.”_
* 💓 **Body:** Burning ears, hollow stomach, wanting to hide in her hostel room.
* 🏷️ **Feelings:** Crushed, exposed, inadequate.

**The Debrief:**
Instead of burying the memory, Ananya sat with the 3-step protocol:
1. **What worked:** Her initial argument on economic policy was well-researched and praised by the judges.
2. **What failed:** She panicked when cross-examined because she had not practiced thinking on her feet under time pressure.
3. **The adjustment:** She joined a weekly impromptu speaking circle to practice 60-second spontaneous responses.

Six months later, Ananya won the zonal inter-college debating trophy. The failure was not the end of her speaking journey—**it was the exact map showing her what to build**.

---

## 5. Think About It (Self-Reflection)

* 💭 **Think of a recent failure or mistake you experienced:** What was your immediate emotional reaction?
* 💭 **Run that event through the 3-step failure debrief:** What is the diagnostic lesson it was trying to teach you?
* 💭 **Why do so many people avoid examining their mistakes honestly?**
"""

# --- TUTORIAL 15: The Power of the Word Yet ---
def format_tut_15(text):
    return """## 1. What is it?

**Two simple habits unlock explosive growth: appending the three-letter word “yet”, and asking for help when you are stuck.**

Notice how adding a single word completely alters psychological meaning:

| Without “Yet” (Fixed & Closed) | With “Yet” (Dynamic & Open) | Impact on the Brain |
| :--- | :--- | :--- |
| _“I can’t do this.”_ | _“I can’t do this **yet**.”_ | Shifts a permanent barrier into a temporary stage of learning. |
| _“I don’t understand statistics.”_ | _“I don’t understand statistics **yet**.”_ | Acknowledges that understanding takes time and practice. |
| _“I am terrible at coding.”_ | _“I am not proficient at coding **yet**.”_ | Removes fixed genetic labels and invites effort. |

> 🔑 **The Word “Yet”:**
> Reminds the nervous system of neuroplasticity: not mastering something today does not mean you never will. It keeps the runway open.

---

## 2. Overcoming the Fear of Asking for Help

In the tutorial, **Tara** could not get her laboratory titrations right. She wanted to ask for guidance, but paralyzed herself with the thought: _“What if they think I’m stupid?”_ So she smiled, pretended everything was fine, and wasted three hours.

### Why We Avoid Asking for Help
* We mistakenly equate asking with **admitting intellectual inferiority**.
* We overestimate the likelihood that others will reject us.
* **The Reality:** Every expert was once an amateur who had the courage to ask questions.

> ⚖️ **Reframing the Act of Asking for Help:**
> * ❌ **Fixed Mindset Lens:** _“Asking for help proves that I lack natural talent and exposes my inadequacy.”_
> * 🌱 **Growth Mindset Lens:** _“Asking for help is a strategic catalyst that accelerates my learning curve and saves valuable time.”_

---

## 3. What Does Research Say?

#### A. People are far more willing to help than you think
In extensive social psychology research by **Dr. Vanessa Bohns at Cornell University**:
* Across thousands of trials, people consistently **underestimated by 50%** the likelihood that strangers, peers, and superiors would agree to help them.
* Asking someone for help actually increases their positive appraisal of your conscientiousness (**The Ben Franklin Effect**).

#### B. The “Not Yet” Grading Experiment
At a high school in Chicago studied by **Dr. Carol Dweck**:
* Instead of assigning failing grades like “F”, students who did not meet standard received the grade **“Not Yet”**.
* Students who received “Not Yet” stayed motivated, revised their assignments, and graduated at significantly higher rates than peers given failing labels.

---

## 4. Case Study: An Everyday Example

**Rahul** was struggling with his cover drive at cricket practice. Every time the bowler pitched outside off-stump, Rahul edged the ball to the slips:
* 🧠 **Thoughts:** _“I’m never going to make the first team. I don’t have natural hand-eye coordination.”_
* 💓 **Body:** Drooping shoulders, slamming his bat into the turf.
* 🏷️ **Feelings:** Dejected, frustrated, isolated.

**The Pivot:**
Rahul caught his internal monologue and added one word: _“I haven’t mastered this drive **yet**.”_
Then he walked over to the senior batsman and asked: _“Bhaiya, my head position is falling over on off-stump deliveries. Can you watch three balls and tell me what my front foot is doing?”_

The senior smiled: _“I had the exact same issue last season. You are lunging too early. Keep your weight on the back foot until the ball bounces.”_
They spent 20 minutes drilling the movement. Rahul’s timing improved immediately. **Adding “yet” kept him from quitting; asking for help gave him the technical solution.**

---

## 5. Think About It (Self-Reflection)

* 💭 **What is a subject or skill where you currently tell yourself “I can’t do this”?** How does adding “yet” feel in your body?
* 💭 **What keeps you from asking for help when you are stuck on a difficult assignment?**
* 💭 **Who is someone in your department or circle you could ask for advice this week?**
"""

# --- TUTORIAL 16: What Happens in Our Brain When We Calm Down ---
def format_tut_16(text):
    return """## 1. What is it?

Have you ever studied diligently for an examination, sat down at your desk, flipped over the paper, and found your mind **completely blank**?

This is not a character flaw or memory defect. It is an evolutionary biological phenomenon called **cognitive hijacking**.

---

## 2. The Fire Alarm vs. The Smart Planner

Your brain relies on two distinct structures when facing stressful challenges:

| Brain Structure | Metaphor in Course | Biological Function Under Calm | Biological Reaction Under High Stress |
| :--- | :--- | :--- | :--- |
| 🚨 **Amygdala** | **The Fire Alarm** | Scans environment quietly for physical threats | Sounds an emergency alarm, releases adrenaline and cortisol |
| 🧠 **Prefrontal Cortex** | **The Smart Planner** | Handles logic, working memory, complex reasoning, and long-term planning | Blood and oxygen are diverted away; executive function shuts down |

> 🐅 **A Tiger or a Test?**
> The human amygdala evolved hundreds of thousands of years ago to protect hunter-gatherers from predatory wild animals. As **Dr. Meera** explains in the tutorial:
> **“Your brain does not know the difference between a tiger and a test.”**
> An exam paper, a viva voce, or a heated conflict triggers the exact same primal alarm. When the alarm screams, the smart planner goes offline.

---

## 3. The Physiology of 4–2–4 Breathing

You cannot simply tell your amygdala to “relax”. But the mind and the body exist in a biological feedback loop: **slowing the breath forces the brain to calm down**.

### 🫁 The 4–2–4 Paced Breathing Protocol

| Phase | Duration & Action | Physiological Mechanism |
| :--- | :--- | :--- |
| 🌬️ **1. Inhale** | **4 Seconds** (smoothly through nose) | Diaphragm expands downward, oxygen enters lower lung lobes. |
| ⏸️ **2. Hold** | **2 Seconds** (gentle pause) | Gas exchange stabilizes; avoids hyperventilation. |
| 💨 **3. Exhale** | **4 Seconds** (slowly through mouth) | Vagus nerve fires acetylcholine, directly slowing cardiac rhythm. |

When your exhale is slow and controlled, the **vagus nerve** releases acetylcholine, directly decelerating heart rate and signaling to the amygdala: _“The threat has passed. You are safe.”_ Within 60 seconds, blood flow returns to the prefrontal cortex.

---

## 4. What Does Research Say?

#### A. The Relaxation Response
In pioneering clinical research by **Dr. Herbert Benson at Harvard Medical School**:
* Controlled diaphragmatic breathing lowered oxygen consumption, normalized blood pressure, and decreased sympathetic nervous system arousal.
* Practicing slow breathing for just two minutes before cognitive testing significantly boosted working memory capacity.

#### B. The Neural Circuitry of Respiration
In a 2017 study published in *Science* by **Stanford University researchers**:
* Scientists identified a specific cluster of neurons in the brainstem (**the breathing pacemaker**) that directly connects breathing cadence to the arousal centers of the amygdala.
* Slow, rhythmic respiration actively switches off arousal circuits in the brain.

---

## 5. Case Study: An Everyday Example

**Vikram** is presenting his final semester project to an external evaluation panel. As he stands at the podium, he looks at the stern faces of the examiners:
* 🚨 **Amygdala Spike:** His heart hammers at 130 bpm, his palms run cold, and his throat constricts. He stares at slide 1 and cannot remember his opening sentence.
* 🧠 **The Old Reaction:** He panics, tries to force words out, stumbles, and feels terror mounting.

**The 60-Second Reset:**
Remembering Tutorial 16, Vikram pauses:
1. He takes a sip of water from the podium glass.
2. He places his feet firmly on the floor and executes three cycles of **4–2–4 breathing** (Inhale 4s, Hold 2s, Exhale 4s).
3. By the third exhale, his pulse steadies. The prefrontal cortex comes back online.
4. He smiles and begins: _“Good morning, esteemed committee members. Today I will present our findings on distributed computing...”_

The presentation was an enormous success. He did not eliminate his adrenaline; **he used biology to turn the volume of the fire alarm down**.

---

## 6. Think About It (Self-Reflection)

* 💭 **Have you ever experienced your mind going blank during an exam or interview?** What was happening physiologically in your amygdala?
* 💭 **Try 4–2–4 breathing right now for 60 seconds:** Notice the subtle shift in your heart rate and jaw tension.
* 💭 **How can you incorporate 1 minute of paced breathing into your daily routine** before high-pressure events?
"""

# --- TUTORIAL 17: Practising Growth Mindset ---
def format_tut_17(text):
    return """## 1. What is it?

**A growth mindset is the deep conviction that your abilities, intelligence, and emotional resilience can be developed through effort, strategic practice, and guidance.**

Its opposite—a **fixed mindset**—is the fatalistic belief that you are born with a set allotment of intelligence and character that cannot fundamentally change.

This final tutorial synthesizes everything Rahul and Tara learned across the entire course into a unified way of living:

---

## 2. Module 3 in One Unified Framework

| Tutorial | Core Scientific Lesson | How It Operates in a Growth Mindset |
| :--- | :--- | :--- |
| **13. Brain Growth** | Practice builds physical myelin and synaptic connections | Effort is the biological vehicle through which competence is created. |
| **14. Magic of Failures** | Errors generate neural diagnostic feedback | Mistakes are information, not verdicts on your worth. |
| **15. The Word 'Yet'** | “Not yet” and asking for help sustain learning | Temporary struggle is a normal milestone on the road to mastery. |
| **16. Calming Down** | Slow 4–2–4 breathing resets the prefrontal cortex | Managing bodily physiology preserves clarity and long-term grit. |

---

## 3. Calm About the Result, Committed to the Process

Before the college cricket team roster was pinned to the notice board, **Rahul** was neither manic with hope nor paralyzed with dread. He stated:
> 🎯 **The Athlete's Philosophy:**
> _“If my name is on the list, I will train hard tomorrow. If my name is not on the list, I will train hard tomorrow.”_

This is the psychological core of a growth mindset:
* **You cannot control external outcomes:** selection committees, economic shifts, exam curves, or weather.
* **You can 100% control your process:** your preparation, your honesty, your daily effort, and how you treat people.

### Humility in Success
A growth mindset applies equally to victory. When Rahul was selected, he did not proclaim: _“I am naturally gifted.”_ He said: _“Whether we win or lose, we will grow.”_ Success is not proof that you can stop striving—it is simply permission to tackle bigger challenges.

---

## 4. What Does Research Say?

#### A. Process Praise vs. Intelligence Praise
In groundbreaking research by **Dr. Carol Dweck and Claudia Mueller**:
* Children praised for **intelligence** (_“You are so smart!”_) subsequently avoided challenging puzzles to protect their smart label, and gave up rapidly when they hit difficulty.
* Children praised for **process and effort** (_“You worked really hard on strategy!”_) enthusiastically chose harder tasks, displayed higher persistence, and outperformed the other group.

#### B. Growth Mindset and Academic Resilience
In a nationwide study published in *Nature* (2019) across **12,000 high school students**:
* A short, science-based growth mindset intervention significantly raised grades in difficult STEM courses and increased advanced course enrollment among struggling students.

---

## 5. Case Study: An Everyday Example

**Rahul and Tara** began the academic year overwhelmed by challenges:
* Tara froze on stage and believed she could never speak publicly.
* Rahul believed cricket selection was purely genetic luck and lost his temper when he struck out.

By integrating the tools of this course:
1. **Emotions as Signals:** They stopped fighting their emotions and started listening to the compass.
2. **Belief Restructuring:** They identified ineffective beliefs and used 7-day logs to rewrite them.
3. **Growth Mindset:** They treated errors as diagnostic data, added “yet” to hard problems, and used slow breathing to stay calm under fire.

At graduation, neither was “fearless” or “perfect”. But both possessed the ultimate human asset: **the confidence that whatever life throws at them, they have the tools to learn, adapt, and grow**.

---

## 6. Think About It (Self-Reflection)

* 💭 **In your own words, what does living with a growth mindset mean to you today?**
* 💭 **How do the four Module 3 tools (brain growth, learning from failure, the word 'yet', and calming down) reinforce one another?**
* 💭 **What is one area of your life where you will commit to process over outcome this month?**
"""

print("Defined all 17 tutorial formatters!")

# --- DB UPDATE EXECUTION ---
with SyncSessionLocal() as session:
    formatters = {
        1: format_tut_1,
        2: format_tut_2,
        3: format_tut_3,
        4: format_tut_4,
        5: format_tut_5,
        6: format_tut_6,
        7: format_tut_7,
        8: format_tut_8,
        9: format_tut_9,
        10: format_tut_10,
        11: format_tut_11,
        12: format_tut_12,
        13: format_tut_13,
        14: format_tut_14,
        15: format_tut_15,
        16: format_tut_16,
        17: format_tut_17
    }
    
    tuts = session.query(Tutorial).filter(Tutorial.course_id == 'personality_dev').order_by(Tutorial.tutorial_number).all()
    for t in tuts:
        tc = session.query(TutorialContent).filter(TutorialContent.tutorial_id == t.id).first()
        if not tc or t.tutorial_number not in formatters:
            continue
        formatter_fn = formatters[t.tutorial_number]
        tc.reading_markdown = formatter_fn(tc.reading_markdown)
        print(f"Formatted Tutorial {t.tutorial_number}: {t.title}")
    
    session.commit()
    print("ALL 17 TUTORIALS SUCCESSFULLY COMMITTED TO POSTGRESQL!")

