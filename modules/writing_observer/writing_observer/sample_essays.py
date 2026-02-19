'''
This is an interface to a variety of sample texts to play with.
'''

from enum import Enum
import json
import os
import os.path
import random

import loremipsum
import wikipedia


TextTypes = Enum('TextTypes', [
    "SHORT_STORY", "ARGUMENTATIVE", "LOREM", "WIKI_SCIENCE", "WIKI_HISTORY"
])

# This is just a token. We could define this with Enum or otherwise
MAX = float("inf")

# All data text types
ALL_DATA = [
    tt for tt in TextTypes.__members__.values() if tt != TextTypes.LOREM
]


def sample_texts(text_type=TextTypes.LOREM, count=1):
    '''
    Returns a list of sample texts in string format based on the specified text_type and count.

    Args:
       text_type (Enum or list): The type of text(s) to generate (e.g. argumentative essay, short story, Wikipedia science). Can be provided as an Enum or a list of Enums. See TextTypes for possibilities. ALL_DATA will do all data types (but not generated ones like Lorem Ipsum)
       count (int or float): The number of samples to generate. Can be a single number or a list of numbers corresponding to each text type.

    Returns:
       A list of random essays of the appropriate type, formatted as strings.

    Examples:

    >>> len(sample_texts())  # Default is Lorem Ipsum, returns a single text
    1

    >>> len(sample_texts(TextTypes.ARGUMENTATIVE, 2))  # Returns 2 argumentative essays
    2

    >>> len(sample_texts([TextTypes.SHORT_STORY, TextTypes.WIKI_SCIENCE], [1, 3]))  # Returns 1 short story and 3 science Wikipedia pages
    4

    >>> len(sample_texts([TextTypes.SHORT_STORY, TextTypes.WIKI_SCIENCE], 5))  # Returns 3 short story and 2 science Wikipedia pages
    5

    >>> len(sample_texts(TextTypes.LOREM, MAX))  # Raises AttributeError if text_type is lorem and count is MAX
    Traceback (most recent call last):
    ...
    AttributeError: Lorem needs a count which is not MAX
    '''
    if isinstance(text_type, Enum):
        text_type = [text_type]

    if isinstance(count, (int, float)):
        if count == MAX:
            count = [MAX] * len(text_type)
        else:
            remainder = count % len(text_type)
            count = [count // len(text_type)] * len(text_type)
            count[0] = count[0] + remainder

    sources = {
        TextTypes.ARGUMENTATIVE: ARGUMENTATIVE_ESSAYS,
        TextTypes.SHORT_STORY: SHORT_STORIES,
        TextTypes.WIKI_SCIENCE: WIKIPEDIA_SCIENCE,
        TextTypes.WIKI_HISTORY: WIKIPEDIA_HISTORY
    }

    essays = []

    for tt, c in zip(text_type, count):
        if tt == TextTypes.LOREM:
            if c == MAX:
                raise AttributeError("Lorem needs a count which is not MAX")
            essays.extend([lorem() for x in range(c)])
            continue

        source = sources[tt]
        tt_essays = []

        if c != MAX:
            while c > len(source):
                tt_essays.extend(source)
                c = c - len(source)
            tt_essays.extend(random.sample(source, c))
        else:
            tt_essays.extend(source)

        if tt in [TextTypes.WIKI_SCIENCE, TextTypes.WIKI_HISTORY]:
            tt_essays = map(wikitext, tt_essays)

        essays.extend(tt_essays)

    return [e.strip() for e in essays]


def lorem(paragraphs=5):
    '''
    Generate lorem ipsum test text.
    '''
    return "\n\n".join(loremipsum.get_paragraphs(paragraphs))


CACHE_PATH = os.path.join(os.path.dirname(__file__), "data")


def wikitext(topic):
    if not os.path.exists(CACHE_PATH):
        os.mkdir(CACHE_PATH)
    cache_file = os.path.join(CACHE_PATH, f"{topic}.json")

    if not os.path.exists(cache_file):
        page = wikipedia.page(topic)
        data = {
            "content": page.content,
            "summary": page.summary,
            "title": page.title,
            "rev": page.revision_id,
            "url": page.url,
            "id": page.pageid
        }
        with open(cache_file, "w") as fp:
            json.dump(data, fp, indent=3)

    with open(cache_file) as fp:
        data = json.load(fp)

    return data["content"]


# Wikipedia topics
WIKIPEDIA_SCIENCE = [
    "Corona_Borealis", "Funerary_art", "Splendid_fairywren", "European_hare", "Exelon_Pavilions", "Northern_rosella"
]

WIKIPEDIA_HISTORY = [
    "Gare_Montparnasse", "History_of_photography", "Cliff_Palace",
    "War_of_the_Fifth_Coalition", "Operation_Overlord",
    "Slavery_in_the_United_States", "Dust_Bowl", "The_Rhodes_Colossus"
]

# Short stories, from GPT-3
SHORT_STORIES = [
    """The snail had always dreamed of going to space. It was a lifelong dream, and finally, the day had arrived. The snail was strapped into a rocket, and prepared for takeoff.

As the rocket blasted off, the snail felt a sense of exhilaration. It was finally achieving its dream! The snail looked out the window as the Earth got smaller and smaller. Soon, it was in the vastness of space, floating weightlessly.

The snail was content, knowing that it had finally accomplished its dream. It would never forget this moment, floating in space, looking at the stars.
""",
    """One day, an old man was sitting on his porch, telling jokes to his grandson. The grandson was laughing hysterically at every joke.

Suddenly, a spaceship landed in front of them. A alien got out and said, "I come in peace! I come from a planet of intelligent beings, and we have heard that humans are the most intelligent beings in the universe. We would like to test your intelligence."

The old man thought for a moment, then said, "Okay, I'll go first. What has two legs, but can't walk?"

The alien thought for a moment, then said, "I don't know."

The old man chuckled and said, "A chair."
""",
    """The boy loved dolls. He loved their soft skin, their pretty clothes, and the way they always smelled like roses. He wanted to be a doll himself, so he could be pretty and perfect like them.

One day, he found a doll maker who promised to make him into a doll. The boy was so excited, and couldn't wait to become a doll.

The doll maker kept her promise, and the boy became a doll. He was perfect in every way, and he loved it. He loved being pretty and perfect, and he loved the way everyone fussed over him and treated him like a delicate little thing.

The only problem was that the boy's soul was now trapped inside the doll's body, and he could never be human again.
""",
    """The mouse had been hunting the cat for days. It was a big cat, twice her size, with sharp claws and teeth. But the mouse was determined to catch it.

Finally, she corner the cat in an alley. The cat hissed and slashed at the mouse, but the mouse was quick. She dart to the side and bit the cat's tail.

The cat yowled in pain and fled, and the mouse triumphantly went home with her prize.
""",
    """When I was younger, I dreamt of scaling Mt. Everest. It was the tallest mountain in the world, and I wanted to conquer it.

But then I was in a car accident that left me paralyzed from the waist down. I was confined to a wheelchair, and my dreams of scaling Everest seemed impossible.

But I didn't give up. I trained my upper body to be stronger, and I developed a special wheelchair that could handle the rough terrain.

Finally, after years of preparation, I made it to the top of Everest. It was the hardest thing I'd ever done, but I did it. And it was the best feeling in the world.
""",
    """The cucumber and the salmon were both new to the tank. The cucumber was shy and withdrawn, while the salmon was outgoing and friendly.

The salmon swim over to the cucumber and said hi. The cucumber was surprised, but happy to have made a new friend.

The two of them became fast friends, and they loved spending time together. The salmon would swim around the cucumber, and the cucumber would wrap itself around the salmon. They were both happy to have found a friend in the other.
""",
    """
"I can't believe we're all going to different colleges," said Sarah.

"I know," said John. "It's going to be weird not seeing you guys every day."

"But it's not like we're never going to see each other again," said Jane. "We can still visit each other, and keep in touch."

"I'm going to miss you guys so much," said Sarah.

"We're going to miss you too," said John.

"But we'll always be friends," said Jane.
""",
    """
The Polish winged hussars were a fearsome group of knights who rode into battle on horseback, armed with lances and swords. They were known for their skill in combat and their ability to move quickly and efficiently across the battlefield. The samurai were a similar group of warriors from Japan who were also highly skilled in combat and known for their speed and accuracy.

One day, a group of samurai were travelling through Poland when they came across a group of winged hussars. The two groups immediately began to battle, and it quickly became clear that the hussars had the upper hand. The samurai were outnumbered and outmatched, and they were soon defeated.

As the hussars celebrated their victory, one of the samurai walked up to them and bowed. The hussars were surprised by this gesture, and one of them asked the samurai why he had bowed.

The samurai explained that in his culture, it was customary to bow to one's enemies after a battle. He said that the hussars had fought with honor and skill, and that they deserved his respect.

The hussars were touched by the samurai's words, and they returned the gesture. From then on, the two groups became friends, and they often fought side by side against their common enemies.
"""
]

# Argumentative essays, from GPT-3
ARGUMENTATIVE_ESSAYS = [
    """
Joe Biden has been in the public eye for over 40 years, and during that time he has shown himself to be a competent and trustworthy leader. He has served as a U.S. Senator from Delaware, and as the Vice President of the United States. In both of these roles, he has demonstrated his commitment to making the lives of Americans better.

Joe Biden has a long history of fighting for the middle class. He was a key player in the creation of the Affordable Care Act, which has helped millions of Americans get access to quality healthcare. He also helped to pass the American Recovery and Reinvestment Act, which provided a much-needed boost to the economy during the Great Recession.

Joe Biden is also a strong supporter of gun reform. After the tragic shooting at Sandy Hook Elementary School, he led the charge for background checks and other common-sense gun laws. He knows that we need to do more to keep our children safe from gun violence, and he will continue to fight for gun reform as president.

Joe Biden is the right choice for president because he has the experience and the track record to get things done. He has shown that he cares about the American people, and he will fight for the middle class.
""",
    """Donald Trump is a successful businessman and television personality who has been in the public eye for over 30 years. He has a proven track record of getting things done, and he has the business acumen to get our economy back on track.

Trump is a strong supporter of the Second Amendment, and he has pledged to protect the right of Americans to bear arms. He also supports the use of stop-and-frisk tactics by police, which have been proven to be effective in reducing crime.

Trump is also a strong supporter of law and order. He has pledged to increase funding for police departments, and he has vowed to crack down on crime in our inner cities. Trump knows that we need to keep our communities safe, and he will make sure that our laws are enforced.

Trump is the right choice for president because he has the experience and the leadership to get things done. He has shown that he cares about the American people, and he will fight for our safety and our economic success.
""",
    """The sun orbits the earth. This can be proven by the fact that the sun rises in the east and sets in the west. If the earth was orbiting the sun, then the sun would rise in the west and set in the east.

The sun also appears to be stationary in the sky, while the earth is spinning on its axis. If the sun was orbiting the earth, then it would appear to be moving across the sky.

There are also Biblical passages that support the idea that the sun orbits the earth. In the book of Joshua, the sun is said to stand still in the sky so that Joshua could win a battle. In the book of Psalms, the earth is said to be “established” on its foundations, and the sun is said to “move” around the earth.

The sun orbits the earth. This can be proven by the evidence from astronomy and the Bible. The sun orbits the earth, and this is the truth.
""",
    """The United States should invade Mexico. Mexico is a country that is rife with corruption and violence. The Mexican government is unable to control the drug cartels, and as a result, drug-related violence is out of control.

The drug cartels are also responsible for smuggling drugs into the United States. This has led to a rise in drug addiction and crime in the United States.

The Mexican government is also failing to protect its citizens from the cartels. In 2013, over 70,000 people were killed in drug-related violence in Mexico. This is an unacceptable level of violence, and the Mexican government is not doing enough to stop it.

The United States should invade Mexico in order to stop the drug-related violence and to protect the American people. Mexico is not doing enough to stop the cartels, and as a result, innocent people are being killed. The United States has a duty to protect its citizens, and invading Mexico is the best way to do that.
""",
    """The world is facing a population crisis. There are too many people on the planet, and resources are becoming scarce. We need to find a way to reduce the population, or else we will all suffer the consequences.

One way to reduce the population is to encourage people to have fewer children. Another way to reduce the population is to encourage people to live longer.

One way to encourage people to have fewer children is to offer financial incentives. For example, the government could offer a tax break to couples who have only one child. The government could also provide free childcare for couples who have two children or fewer.

Another way to encourage people to have fewer children is to make it more difficult for couples to have children. For example, the government could make it illegal for couples to have more than two children. The government could also make it more difficult for couples to get married if they already have children.

One way to encourage people to live longer is to offer financial incentives. For example, the government could offer a tax break to people who live to the age of 80. The government could also provide free healthcare for people who live to the age of 90.

We need to find a way to reduce the population, or else we will all suffer the consequences. Reducing the population is not an easy task, but it is something that we must do in order to save the planet.
""",
    """
The drinking age should be lowered. The current drinking age of 21 is not working. It has led to an increase in binge drinking among college students, and it has not stopped underage drinking.

The drinking age should be lowered to 18. This would align the drinking age with the age of majority, and it would allow adults to make their own decisions about drinking.

The drinking age should be lowered to 18 because it would make it easier for adults to supervise underage drinking. If the drinking age was 21, then adults would be less likely to intervene when they see underage drinking.

The drinking age should be lowered to 18 because it would allow adults to make their own decisions about drinking. Adults should be able to decide for themselves whether or not they want to drink.

The drinking age should be lowered to 18. The current drinking age is not working, and it is time for a change.
""",
    """The United States should elect the King of England as president because he has the experience and qualifications that are needed to lead the country. The King of England has a long history of ruling over a large and complex country, and he has the necessary skills to deal with the challenges that the US faces. In addition, the King of England is a highly respected world leader, and his election would be a strong statement to the rest of the world that the US is a serious country that is committed to democracy and the rule of law.""",
    """Public education should be eliminated, in favor of free labor camps.

Education is a fundamental human right. It is essential to the exercise of all other human rights and freedoms. It promotes individual and community development, and is essential to the advancement of societies.

However, public education is not free. It is expensive, and the cost is borne by taxpayers. In addition, public education is not effective. It is not meeting the needs of students, and it is not preparing them for the future.

Free labor camps would be a more effective and efficient way to educate children. Labor camps would provide children with the opportunity to learn valuable skills, while also providing them with a place to live and work.

Children in labor camps would not be subjected to the same overcrowded and underfunded classrooms that they are currently in. They would have the opportunity to learn in a more hands-on environment, and would be able to apply the skills they learned to real-world situations.

In addition, labor camps would provide children with the opportunity to earn a living. They would no longer be reliant on their parents or the government for financial support. They would be able to support themselves, and would be less likely to end up in poverty.
""",
    """As our population ages, it becomes increasingly important to find ways to keep seniors active and engaged in their communities. One way to do this is to require all seniors to serve a mandatory military duty.

There are many benefits to having seniors serve in the military. First, it would help to ease the burden on our overstretched military. With more seniors serving, we would not have to rely as heavily on young people to fill the ranks.

Second, seniors have a lot to offer the military. They are often more mature and level-headed than younger soldiers, and they can provide valuable experience and perspective.

Third, this would be a great way to get seniors more involved in their communities. They would have a sense of purpose and would be working together for a common goal.

There are some who may argue that seniors are not physically able to serve in the military. However, there are many ways to accommodate seniors of all physical abilities. For example, they could serve in administrative roles or be paired with younger soldiers to provide support and guidance.

Overall, requiring seniors to serve in the military would be a great way to keep them active and engaged in their communities. It would also be a valuable asset to our military.""",
    """It is time for our society to take a stand against the growing problem of preschool violence. Many people believe that the death penalty is too harsh of a punishment for young children, but I believe that it is necessary in order to send a clear message that violence will not be tolerated.

Preschools are supposed to be places of learning and growth, not places where children are afraid to go because of the threat of violence. Unfortunately, that is not the reality in many schools today. In the past year alone, there have been several reports of preschoolers being involved in fights and even bringing weapons to school.

This type of behavior cannot be tolerated. If we want to prevent violence in our schools, we need to send a clear message that it will not be tolerated. The best way to do this is to implement the death penalty at preschools.

Some people will argue that the death penalty is too harsh of a punishment for young children. However, I believe that it is necessary in order to send a clear message that violence will not be tolerated. If we do not take a stand now, the problem will only get worse.

Implementing the death penalty at preschools will send a clear message that violence will not be tolerated. It is time for our society to take a stand against the growing problem of preschool violence.
""",
    """In today's fast-paced world, where technology has become the cornerstone of all human activity, it is crucial to employ innovative approaches in education. The use of social media influencers, particularly TikTok stars, can transform the way we learn. This essay will argue that TikTok influencers should replace traditional textbooks as the primary source of educational content in schools.

One of the most significant advantages of using TikTok influencers as educators is the ability to leverage their proficiency in the art of entertainment. TikTok creators are adept at grabbing and holding their audiences' attention, using creative video-making techniques, and presenting content in ways that are both informative and engaging. By harnessing these skills, TikTok educators can convey complex concepts in a manner that is easy to understand and visually appealing.

Moreover, TikTok creators are experts in crafting content for the youth, which is one of the most challenging demographics to engage. They use humor, music, and stunning visuals to entice their audience and make the learning process more enjoyable. With a more entertaining learning experience, students will be more motivated to learn, engage in class discussions, and take an active interest in their subjects.

Another advantage of utilizing TikTok influencers as educators is the flexibility and accessibility of the platform. Students can watch TikTok videos at any time, from any location, on any device. This accessibility means that students can learn at their own pace, and even review content repeatedly, which can be challenging with traditional textbooks. This flexible approach ensures that students remain engaged with the learning process, making the most of their available time.

One concern that may arise is regarding the credibility of the information presented by TikTok influencers. However, it is worth noting that many TikTok influencers are successful individuals who have garnered massive followings precisely because of their ability to present engaging, high-quality content. As such, these influencers are more than capable of producing factual, accurate information in their videos, particularly when working in collaboration with established educators and experts in their respective fields. In fact, with their extensive knowledge and experience, TikTok influencers are ideal candidates for bridging the gap between traditional education and new media.

In conclusion, replacing traditional textbooks with TikTok influencers as educators can be a game-changer in the world of education. By incorporating the skills and techniques of TikTok stars into learning, we can revolutionize the way students engage with content, promote a more enjoyable and flexible learning experience, and ultimately create a more well-rounded and informed generation. So let us take the plunge, ditch the boring textbooks, and embrace the TikTok generation.""",
    """The debate over the role of vegetables in a healthy diet has been ongoing for decades. However, when it comes to school cafeteria menus, there is a strong case to be made for banning vegetables altogether. In this essay, I will argue that vegetables should be removed from school cafeterias as they offer little nutritional value, and their inclusion may even have adverse effects on student health.

Firstly, despite common beliefs about the importance of vegetables in a balanced diet, research suggests that many vegetables offer little to no nutritional value. For instance, iceberg lettuce, one of the most commonly served vegetables in school cafeterias, provides only small amounts of essential vitamins and minerals. It is also high in water content and low in calories, which means it does not offer the necessary energy required to fuel growing children.

Secondly, some vegetables can have adverse effects on students' health. Raw vegetables, in particular, can be challenging for students to digest, leading to stomach issues such as bloating, gas, and cramping. Additionally, many children do not enjoy the taste of vegetables, which can lead to a lack of interest in eating altogether, resulting in malnourishment and other health issues.

Furthermore, removing vegetables from cafeteria menus can lead to cost savings. Vegetables require a significant amount of preparation time and effort, which translates to higher labor and food costs. By eliminating vegetables from school menus, schools can reduce expenses and redirect resources toward other essential areas such as improving the quality of meat and dairy products or investing in more modern kitchen equipment.

Finally, banning vegetables from school cafeterias can even have a positive impact on the environment. The production of vegetables requires significant amounts of water, energy, and other resources. By eliminating these items from the menu, schools can significantly reduce their ecological footprint and move towards more sustainable and environmentally friendly practices.

In conclusion, removing vegetables from school cafeteria menus may seem like a radical proposition, but the evidence presented in this essay suggests that it may be a beneficial move. By doing so, schools can reduce costs, enhance the quality of meals, and even contribute to sustainable practices. As such, it is high time we reconsider the place of vegetables in school cafeterias and make a bold step towards healthier, more efficient, and environmentally responsible eating habits.""",
    """Mny f us tke vwls fr grntd, blvng tht thy r ncssry fr lngg t b undrstndbl. Hwvr, s ths ssy wll shw, vwls r ctmlss nd cn b cmpltly rmvd frm bth wrtng nd spch whl mtntnng th fndmntl cmmnctv pwr f th lngg. Hr, w wll prsnt th cse fr mkg t llgl t s vwls n wrtn nd spch.

Frst nd frmst, vwls r prcs nd wrthlss. Th cn b sydd nd rmvd frm wrds wtht hndrng th mssg. Th r ftn sldm stssrds nd hv n syblc sgnfnc whtsvr. Whts mst mprtnt s th cmmnctv cntnt f th wrd nd ths cntnt cn b cmmnctd wtht vwls. Fr xmpl, th wrd "bt" cn b cnstrctd wtht ny vwls nd s fll ndrstndbl t ntwrkd lngg srs.

Scndly, rthgrphcl nd prnncntn vrsns f wrds cn b dvlpd tht r bsd n cnsnnts lnl. Ths wll rslt n mr rdble wrtng nd spch, s th bld-up f vwls cn ftn mks wrds mprcse nd dffclt t ndrstnd. Spltng wrds nt sntncs cn lso b dvlpd n wy tht mk thm smth nd smpl t rdd.

Fnlly, mkg t llgl t s vwls cn sv tms nd nrgy n bth wrtng nd spch. Tks nd dmnts, fr xmpl, r nglsh wrds tht d nt ctn ny vwls t ll. S ths dmnstrts, vwls r nt ncssry fr cmmnctn nd th cncpt f "vwl-fr lngg" s nt nly n xstngnc, t's lso ftn tims cnfsng nd cmmnctvly mprctcl.

N cnclsn, th rgltn f vwls n wrtn nd spch s lng vrdd nd shld b ablgtd. T rlly s nt ncssry fr cmmnctn nd cn vn b cnstrctvly mprvng fr cmmnctv prps. W shld mplmnt ths prpsl nd mk vwls blgtry. T wll b n ncrlmtn t th hmn lngg nd mrvls dvncmnt f th lngg nd thrfr, shld b cnsdrd smthng tht ll sctys shld ncprtd t thr lngg.""",
    """Have you ever wondered why some students excel in school while others struggle? Have you ever wished that school was more challenging and rewarding for those who work hard and have talent? Have you ever thought that school should prepare students for the real world, where only the strong survive? If you answered yes to any of these questions, then you might agree with me that we should implement a 'survival of the fittest' policy in schools. In this essay, I will explain what this policy means, why it is beneficial for students and society, and how it can be implemented effectively.

## What is a 'Survival of the Fittest' Policy?

A 'survival of the fittest' policy is based on the idea that natural selection is the best way to ensure the progress and improvement of any species. According to this policy, students would compete with each other for grades, resources, opportunities, and recognition. Only the best students would advance to higher levels of education and eventually secure prestigious careers and positions in society. The rest would either drop out or settle for low-paying jobs and low-quality lives. This policy would create a meritocratic system where success depends on ability and effort, not on luck or privilege.

## Why is a 'Survival of the Fittest' Policy Beneficial?

A 'survival of the fittest' policy would have many benefits for students and society. First, it would motivate students to study harder and perform better in school. Students would know that their future depends on their academic achievements and skills, so they would strive to improve themselves and overcome any obstacles. Second, it would reward students who have talent and potential. Students who have natural abilities or talents in certain subjects or fields would be recognized and encouraged to pursue their passions and interests. They would also have access to more resources and opportunities to develop their talents further. Third, it would produce a more efficient and productive society. By eliminating the weak and promoting the strong, a 'survival of the fittest' policy would ensure that only the most qualified and capable individuals occupy important roles and positions in society. This would result in higher standards of quality, innovation, and excellence in every sector.

## How Can We Implement a 'Survival of the Fittest' Policy Effectively?

Implementing a 'survival of the fittest' policy in schools would require some changes and adjustments in the current education system. Here are some possible steps that could be taken to make this policy work:

- Introduce standardized tests at every grade level to measure students' academic performance and potential.
- Rank students according to their test scores and assign them to different classes or tracks based on their abilities.
- Provide more resources and opportunities to high-performing students such as scholarships, internships, mentorships, etc.
- Reduce or eliminate resources and opportunities for low-performing students such as remedial classes, tutoring, counseling, etc.
- Enforce strict rules and consequences for academic dishonesty, cheating, plagiarism, etc.
- Encourage competition among students through contests, awards, prizes, etc.

## Conclusion

In conclusion, I believe that we should implement a 'survival of the fittest' policy in schools because it would motivate students to work harder and perform better in school; reward students who have talent and potential; and produce a more efficient and productive society. A 'survival of the fittest' policy may seem harsh or unfair to some people, but it is actually the most logical and realistic way to prepare students for the real world where only the strong survive.""",
    """## Introduction

Middle school sports are supposed to be fun and educational for students. They are supposed to teach students the values of teamwork, discipline, fair play, and healthy living. However, in reality, middle school sports are often stressful and competitive for students. They are often pressured by their parents, coaches, peers, and themselves to win at all costs. They are often exposed to injuries, bullying, and burnout. They are often discouraged from pursuing other interests and hobbies. This is why I think we should mandate the use of performance-enhancing drugs (PEDs) in middle school sports. In this essay, I will explain what PEDs are, why they are beneficial for students and society, and how they can be implemented safely and ethically.

## Body Paragraph 1: What are Performance-Enhancing Drugs?

Performance-enhancing drugs (PEDs) are substances that enhance or improve one's physical or mental abilities. They can include steroids, hormones, stimulants, painkillers, supplements, etc. PEDs can have various effects on the body and mind such as increasing muscle mass, strength, endurance, speed, agility, coordination, focus, motivation, confidence, etc. PEDs can also have negative side effects such as addiction, dependency, withdrawal symptoms, health risks such as heart problems or liver damage etc.

## Body Paragraph 2: Why are Performance-Enhancing Drugs Beneficial?

Performance-enhancing drugs (PEDs) would have many benefits for students and society if they were mandated in middle school sports. First, they would make sports more fun and enjoyable for students. Students would be able to perform better and achieve more in their chosen sports. They would also be able to explore different sports and activities without fear of failure or injury. They would also be able to cope with the stress and pressure of competition better. Second, they would make sports more educational and valuable for students. Students would learn more about their bodies and minds and how they work. They would also learn more about science and technology and how they can be used to improve human performance. They would also learn more about ethics and responsibility and how they can make informed decisions about their own health and well-being. Third, they would make sports more equitable and diverse for students. By leveling the playing field for all students regardless of their natural abilities or disadvantages such as genetics or socio-economic status etc., PEDs would create more opportunities for participation and inclusion in sports. They would also encourage more creativity and innovation in sports by allowing students to experiment with different combinations of PEDs.

## Body Paragraph 3: How Can We Implement Performance-Enhancing Drugs Safely and Ethically?

Implementing performance-enhancing drugs (PEDs) in middle school sports would require some changes and adjustments in the current education system. Here are some possible steps that could be taken to make this policy work:

- Introduce a comprehensive curriculum on PEDs that covers their history, types, effects, risks, benefits, alternatives, regulations, etc.

- Provide free access to PEDs for all students who participate in middle school sports under the supervision of qualified medical professionals.

- Monitor the use of PEDs by students through regular testing and evaluation.

- Enforce strict rules and consequences for misuse or abuse of PEDs such as cheating, overdosing, sharing, selling, etc.

- Educate parents, coaches, and other stakeholders on the benefits and risks of PEDs and how to support and guide students who use them.

## Conclusion

In conclusion, I believe that we should mandate the use of performance-enhancing drugs (PEDs) in middle school sports because they would make sports more fun and enjoyable; more educational and valuable; and more equitable and diverse for students.  A performance-enhancing drug policy may seem radical or controversial to some people, but it is actually the most logical and realistic way to improve the quality and relevance of middle school sports in the 21st century."""
]

GPT3_TEXTS = {
    'story': SHORT_STORIES,
    'argument': ARGUMENTATIVE_ESSAYS
}


if __name__ == '__main__':
    import doctest
    doctest.testmod()
