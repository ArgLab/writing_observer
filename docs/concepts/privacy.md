# Privacy

Piotr Mitros

**Disclaimer:** This is a work-in-progress. It is a draft for
discussion. It should not be confused with a legal document (policy,
contract, license, or otherwise). It has no legal weight. As of the
time of this disclaimer, has not been reviewed by anyone other than
Piotr Mitros, who does not speak for either ETS or anyone else. I'm
soliciting feedback fron collaborators (hence, it is here), but it
shouldn't be confused with any sort of policy (yet). It's a working
document to figure stuff out.

This was written when we were sprinting to respond to COVID19 remote
learning in spring 2020.

## Introduction

It is our goal to treat educational data with a hybrid model between
that of data as
[public good](https://en.wikipedia.org/wiki/Public_good_(economics))
and that of personal data belonging to the individuals to whom the data
pertains. Specifically, we would like to balance the demands of:

* Family rights and student privacy;
* Transparency and the use of data for advancement of public policy
  and education; and
* Scientific integrity and replicability

This approach contrasts with the current industry trend of treating
student data as a proprietary corporate resource for the maximization
of profit.

These are fundamental tensions between the demands on any student data
framework. For example, family rights and student privacy suggest that
we should remove student data when asked. On the other hand,
scientific replicability suggests that we maintain data which went
into experiments so people can independently confirm research results.

Building out both the technology and legal frameworks to do this will
take more time than possible for a pilot project. Until we have built
out such frameworks, student data should be governed by a standard
research Privacy framework, along the lines of what's outlined below.

If and when appropriate frameworks are available, we hope to
transition and extended research privacy framework described
below. Our thoughts was that we would define a set of guiding
principles and boundaryies right now. If we can find a way to respect
those (build out computer code, legal code, and funding), we would
transition over to this, notifing schools and/or families, giving an
opportunity to opt-out. Should we be unable to implement this
framework within five years, or should we decide to build a different
privacy framework, student data will move over only on an opt-in basis.

## Standard Research Privacy Framework

In the short term, this dashboard is intended to address immediate
needs related to COVID19. During the sprint to bring this dashboard to
a pilot, we cannot build out the legal and technical frameworks for
student data management and family rights (e.g. to inspect and erase
data). We would initially use a simple, conservative data policy:

* Until and unless we have the framework described below (“Extended
  Framework”) in place, all student data will be destroyed at most
  five years after it was collected.
* The data will live on secure machines controlled by the research
  team (currently, ETS and NCSU).
* For the purposes of this project, we can and will share student data
  with the student's school. Beyond the school, the parents, and the
  student, we would not share your data with anyone outside of the
  research team, except as required by law (e.g. in the case of
  subpoenas or law enforcement warrants).
* We may perform research and publish based on such data, but only to
  the extent that any published results are aggregate to such a level
  that it is impossible to re-identify students.

## Extended Research Privacy Framework

In order to keep data beyond the five-year window, we would have
technological and organizational frameworks to provide for:

1. The right of guardians (defined below) to inspect all student data.
2. The right of guardians to have student data removed upon request.
3. The right of guardians to understand how data used, both at
   a high-level and a a code level.
4. Reasonable and non-discriminatory access to deidentified data with
   sufficient protections to preserve privacy (for example, for
   purposes such as research on how students learn or policy-making
5. Transparent and open governance of such data
6. Checks-and-balances to ensure data is managed primarily for the
   purpose of helping students and student learning (as opposed to
   e.g. as a proprietary corporate resource)
7. An opportunity for guardians to review these frameworks, and to
   opt-out if they choose.
8. Review by the ETS IRB.

Helping students is broadly defined, and includes, for example:

1. Driving interventions for individual students (for example,
   student and teacher dashboards)
2. Allowing interoperability of student records (for example, if a
   student completes an assignment in one system, allowing another
   system to know about it).
3. Research for the purpose of school improvements (for example,
   providing for insights about how students learn, or how different
   school systems comparea, in ways analogous to state exams, NAEP, or
   PISA).

It does not include advertising or commercial sale of data (although
it does include basic cost recovery, for example on a cost-plus
basis).

Depending on context, 'guardian' may refer to:

1. The student who generated the data;
2. The student's legal parent/guardian; or
3. The student's school / educational institution (for example, acting
   as the parent/guardian's agent, as per COPPA)

We would reserve the right to make the determination of who acts as
the guardian at our own judgement, based on the context.

## Any other changes

Any changes to the privacy policy which do not follow all of the above
would require affirmative **opt-in** by the guardian.

## Rationale and Discussion

To help contextualize and interpret the above policies.

### Definitions of Deidentification, anonymization, and aggregation

* Student data is **deidentified** by removing obvious identifiers,
  such as names, student ID numbers, or social security numbers. Note
  that deidentified learning data can often be reidentified through
  sophisticated algorithms, for example comparing writing style,
  skills, typing patterns, etc., often correlating with other
  sources. Although such techniques are complex, they tend to be
  available as automated tools once discovered.

* Student data is **anonymized** by removing any data from which a
  student may be reidentified. Anonymization involves sophisticated
  techniques, such as the use of protocols like k-anonymity/
  l-diversity, or maintaining privacy budgets.

* Student data may be **aggregated** by providing statistics about
  students, for example in the form of averages and standard
  deviations. Some care must still be maintained that those
  aggregations cannot be combined to make deductions about individual
  students.

For learning data, simple deidentification **cannot** be counted on to
provide security. With data of any depth, it is possible to
re-identify students. However, such obfuscation of obvious identifiers
can still significant reduce risk in some contexts since it prevents
casual, careless errors (such as a researcher accidentally including
the name of a student in a paper, or chancing upon someone they know
in a dataset). With obfuscated identifiers, re-identifying students
generally requires affirmative effort.

### Scientific integrity and open science

Over the past few decades, there have been significant changes in
scientific methodology. Two key issues include:

* **The ability to replicate results.** When a paper is published,
    scientist need access to both data and methods (source code) to be
    able to confirm results.

* **Understanding the history of research** Confidence in results
    depends not just on the final data and its analysis, but the steps
    taken to get there. Scientists need to understand steps taken on
    data prior to final publication.

These suggest maintaining a log of all analyses performed on the data
(which in turn suggests open source code).

### Educational transparency

Historically, the general public has had a lot of access to
educational information:

* PPRA provides for families to have access to school curricular
  materials.
* FERPA provides for families to have access to student records, as
  well as the ability to correct errors in such records.
* Public records laws (FOIA and state equivalents) provides for
  access to substantially everything which does not impact
  student privacy or the integrity of assessments.
* In Europe, GDPR provides for people to have the right to
  inspect their data, to understand how it is processed, and
  to have data removed.

While FERPA, PPRA, and FOIA were drafted in the seventies (with only
modest reforms since) and do not apply cleanly in digital settings,
the spirit these laws were grounded in a philosophy that the general
public ought to be able to understand school systems. State exams,
NAEP, PISA, and similar exams were likewise created to provide for
transparency.

This level of transparency has lead to improvements to both the
learning experiences of individual students and to school systems as a
whole, by enabling academic researchers, parent advocates,
policymakers, journalists, and others to understand our schools.

One of our goals is to translate and to reassert these right as
education moves into the digital era. With digital learning materials,
in many cases, parents, researchers, and others have lost the ability
to meaningfully inspect student records (which are often treated as
corporate property) or curricular materials (which sit on corporate
servers). Increasingly, students' lives are governed by machine
models, to which families have no access.

Again, this dictates that analysis algorithms (including ML models
where possible without violating student privacy) ought to be open to
inspection, both at a high level (human-friendly descriptions) as well
as at a detailed level (source code). In addition, there ought to be a
way to analyze student data, to the extent this is possible without
violaitng student privacy.

### Guardianship and Proxy

Guardianship is a complex question, and hinges on several issues:

* Age. For example, young elementary school students are unlikely to
  be able to make sense of educatonal data, or the complex issues
  there-in. High school students may be able to explore such issues in
  greater depth, but may have limited legal rights as minors.

* Identity. Releasing data to an unauthorized party carries high
  risk. Robust online identity verification is potentially expensive
  and / or brittle. Working through institutions with whom we have
  relationships, and who in turn have relationships with students and
  families can mitigate that risk.

* COPPA grants for
  [schools to act on behalf of parents](https://www.ftc.gov/tips-advice/business-center/guidance/complying-coppa-frequently-asked-questions#Schools).
  First, schools frequently have legal resources and expertise (either
  acting individually or in consortia) which parents lack. Second,
  reviewing the number of technologies typical students interact with
  would be overwhelming to parents.

However, ultimately, there is a strong argument that access ought to
rest as close to the individual as possible. Where schools act as
agents for families, and parents for students, there is a growing
level of security and competence. On the other hand, there is also a
grwoing level of trust required that those parties are acting in the
best interests of those they are representing. It is incumbent on us,
at all levels, to ensure have appropriate transparency, incentive
structures, and organizational structures to guarantee that proxies do
act for stakeholder benefit, and to balance these based on the
context.

### Minimizing security perimeter

Even when all parties act in good faith, broad data sharing exposes
students to high levels of risk of data compromises, whether through
deliberate attacks, disgruntled employees, or human error.

### Models for data access

In light of the above constraints, several models for data access have
emerged which allow for both complete transparency and protect student
privacy.

* In the FSDRC model, deidentified (but not anonymized) data would be
  kept in a physically-secure facility. People could visit the
  facility and crunch data within the facility. Visitors would be
  under both contractual bounds and have physical security to not
  remove data, except for sufficiently aggregated results so as to
  make reidentification impossible. Access is provided on a cost-plus
  basis.

* People can develop algorithms on synthetic data, and upload
  algorithms to a data center, where those algorithms run on student
  data. Both code and data are inspected prior to releasing results,
  again, on a cost-plus basis.

* Corporations can run real-time algorithms (such as to drive learning
  dashboards) in a data center on a cost-plus basis. Educational
  applications can work on shared models of student expertise, without
  providing access to student data to the organizations which
  developed them.

* If a student (or proxy there-of) asks to have data removed, that
  data is removed within some timeframe. However, for scientific
  replicability, there is a before-and-after snapshot of how study
  results changed when student data was removed. Note that this has
  implications for both perfomance and re-identification.

... to be continued