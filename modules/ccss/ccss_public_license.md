# Common Core License Disclaimer

If you are using this package, you are also presumably using the Common Core State Standards as well. For reference, a copy of the license text from:

   https://www.thecorestandards.org/public-license/
   
This was downloaded 3/30/2024.

Note that this text applies to the original Common Core standards (not the Python code / Python package we developed, which is open-source). We include this so that you can evaluate whether or not it is appropriate for your use, and the extent to which it applies.

I'll provide a little bit of background. CCSS made the unfortunate decision not to use a standard license but draft a custom one. This places a lot of uses in legally-murky territory unless you have proper legal advice for what is and isn't okay. The license text, while pleasantly short, repeats mistakes of past licenses, and more critically, isn't well-understood (like a vetted license).

Note that I am not a laywer, and disclaimer this has not been reviewed by lawyers. Any of this may be incorrect. It is not here as legal advice, but rather so that you can understand why it might be important to talk to a lawyer before adopting CCSS for your own curriculum or technology system, and give the background which might be helpful to hold that conversation.

## CCSS "Public License" issues
===============================

Broad use of CCSS standards is permitted under the so-called ["Public License"](https://www.thecorestandards.org/public-license/), also included below for reference. This license has several problems, the dominant of which it carries a use restriction (namely that it only permits "purposes that support the Common Core State Standards Initiative").

This might not seem like a big deal to a lay reader, but it has several severe problems:

* **Compatibility with OERs**. Most OER, free software, and open-source licenses do not permit the addition of use restrictions. This does not permit uses of CCSS-derivative works in, for example, a CC-BY-SA curricular resource, and the license [non-free](https://en.wikipedia.org/wiki/The_Free_Software_Definition).

* **Poor legal text** The phrasing here is ill-defined. If you're making a piece of curriculum which diverges from Common Core, is that supporting the initiative? At what point does innovating diverge enough that you're in violation? Legally-ambiguous license text is problematic because to defend yourself in court, you're looking at hundreds of thousands of dollars in legal fees.

** **Discouraging progress** Common Core is an excellent starting point to start developing curriculum and innovating from. Ideally, progress would feed back into Common Core. This is discouraged by this license.

The above is based on hard-learned lessons from similar licenses in other projects. CC-SA-NC has some of the same bugs as this license text, for example, but CC-SA-NC has been examined by armies of lawyers, and we at least understand how those play out. Here, you're on _terra incognita_.

Generally, these sorts of legal minefields tend to crop up a lot in custom licenses, as CCSS chose to use. That's why most projects use standard, well-understood licenses. I could write a diatribe about how this license text seems to confuse contract law and copyright law, but I would leave that to a proper lawyer.

I was disappointed that CCSS created a custom, ill-understood license which may expose you to legal liability if you adopt CCSS.

Why this might not apply
========================

Licenses often try to do things not really kosher with copyright law, and this license does smell fishy. A lawyer should review for whether / when a license is required. Places to look:

* Under section 105 of the Copyright Act of 1976, works created by the federal government are not entitled to domestic copyright protection under U.S. law and are therefore in the public domain. I have no idea how this relates to an initiative sponsored by the National Governors Association and the Council of Chief State School Officers. It is odd that a tax-funded initative would not be open, though.
* There's a complex set of law about when license requirements kick in. To be specific, copyright applies to specific actions such as copying and ditribution. Many anticipated uses might not touch on those.
* Data cannot be copyrighted, but creative works can. In a case like this one, we are extracting data from a creative work. The data includes descriptive text, to a non-lawyer, it is clear as mud where the line is drawn.
* Most uses of CCSS are probably not significant enough to constitute a derivative work, under fair use.
* Specifically, cases like *Google LLC v. Oracle America, Inc.* suggest uses like this package might fall entirely under the fair use exemption.

The problem here is that even if the above arguments are right, adopting CCSS likely requires legal review, which is thousands of dollars of lawyer time. If CCSSO disagrees with your lawyer and sues, proving that in court requires hundreds of thousands or millions of dollars. Most educational organizations don't have that.

At some point, hopefully, NGA/CCSSO should fix its license, since excluding CCSS from use in most OERs was probably not the intended effect of adopting this license, and is likely to discourage broad use of CCSS.

Indeed, I suspect it has as much uptake as it does simply because a lawyer never did such a review, and I'm unaware of CCSSO suing anyone yet.

***

## Actual Text of the CCSS "Public License"

### Public License

#### Introduction

THE COMMON CORE STATE STANDARDS ARE PROVIDED UNDER THE TERMS OF THIS PUBLIC LICENSE. THE COMMON CORE STATE STANDARDS ARE PROTECTED BY COPYRIGHT AND/OR OTHER APPLICABLE LAW. ANY USE OF THE COMMON CORE STATE STANDARDS OTHER THAN AS AUTHORIZED UNDER THIS LICENSE OR COPYRIGHT LAW IS PROHIBITED.

ANY PERSON WHO EXERCISES ANY RIGHTS TO THE COMMON CORE STATE STANDARDS THEREBY ACCEPTS AND AGREES TO BE BOUND BY THE TERMS OF THIS LICENSE. THE RIGHTS CONTAINED HEREIN ARE GRANTED IN CONSIDERATION OF ACCEPTANCE OF SUCH TERMS AND CONDITIONS.

#### License Grant

The NGA Center for Best Practices (NGA Center) and the Council of Chief State School Officers (CCSSO) hereby grant a limited, non-exclusive, royalty-free license to copy, publish, distribute, and display the Common Core State Standards for purposes that support the Common Core State Standards Initiative. These uses may involve the Common Core State Standards as a whole or selected excerpts or portions.

#### Attribution; Copyright Notice

NGA Center/CCSSO shall be acknowledged as the sole owners and developers of the Common Core State Standards, and no claims to the contrary shall be made.

Any publication or public display shall include the following notice: “© Copyright 2010. National Governors Association Center for Best Practices and Council of Chief State School Officers. All rights reserved.”

States and territories of the United States as well as the District of Columbia that have adopted the Common Core State Standards in whole are exempt from this provision of the License.

#### Material Beyond the Scope of the Public License

This License extends to the Common Core State Standards only and not to the examples. A number of the examples are comprised of materials that are not subject to copyright, such as due to being in the public domain, and others required NGA Center and CCSSO to obtain permission for their use from a third party copyright holder.

With respect to copyrighted works provided by the Penguin Group (USA) Inc., duplication, distribution, emailing, copying, or printing is allowed only of the work as a whole.

McGraw-Hill makes no representations or warranties as to the accuracy of any information contained in the McGraw-Hill Material, including any warranties of merchantability or fitness for a particular purpose. In no event shall McGraw-Hill have any liability to any party for special, incidental, tort, or consequential damages arising out of or in connection with the McGraw-Hill Material, even if McGraw-Hill has been advised of the possibility of such damages.

#### Representations, Warranties and Disclaimer

THE COMMON CORE STATE STANDARDS ARE PROVIDED AS-IS AND WITH ALL FAULTS, AND NGA CENTER/CCSSO MAKE NO REPRESENTATIONS OR WARRANTIES OF ANY KIND, EXPRESS, IMPLIED, STATUTORY OR OTHERWISE, INCLUDING, WITHOUT LIMITATION, WARRANTIES OF TITLE, MERCHANTIBILITY, FITNESS FOR A PARTICULAR PURPOSE, NONINFRINGEMENT, ACCURACY, OR THE PRESENCE OR ABSENCE OF ERRORS, WHETHER OR NOT DISCOVERABLE.

#### Limitation on Liability

UNDER NO CIRCUMSTANCES SHALL NGA CENTER OR CCSSO, INDIVIDUALLY OR JOINTLY, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, CONSEQUENTIAL, OR PUNITIVE DAMAGES HOWEVER CAUSED AND ON ANY LEGAL THEORY OF LIABILITY, WHETHER FOR CONTRACT, TORT, STRICT LIABILITY, OR A COMBINATION THEREOF (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THE COMMON CORE STATE STANDARDS, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH RISK AND POTENTIAL DAMAGE. WITHOUT LIMITING THE FOREGOING, LICENSEE WAIVES THE RIGHT TO SEEK LEGAL REDRESS AGAINST, AND RELEASES FROM ALL LIABILITY AND COVENANTS NOT TO SUE, NGA CENTER AND CCSSO.

#### Termination

This License and the rights granted hereunder will terminate automatically as to a licensee upon any breach by that licensee of the terms of this License.

NGA Center and CCSSO reserve the right to release the Common Core State Standards under different license terms or to stop distributing the Common Core State Standards at any time; provided, however that any such election will not serve to withdraw this License with respect to any person utilizing the Common Core State Standards pursuant to this License.

#### Miscellaneous

This License shall be construed in accordance with the laws of the District of Columbia, without regard to conflicts principles, and as applicable, US federal law. A court of competent jurisdiction in Washington, DC shall be the exclusive forum for the resolution of any disputes regarding this License, and consent to the personal and subject matter jurisdiction, and venue, of such court is irrevocably given.

If any provision of this License is invalid or unenforceable under applicable law, it shall not affect the validity or enforceability of the remainder of the terms of this License, and such provision shall be reformed to the minimum extent necessary to make such provision valid and enforceable.

No term or provision of this License shall be deemed waived and no breach consented to unless such waiver or consent shall be in writing and signed by authorized representatives of NGA Center and CCSSO.
