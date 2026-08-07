# Singapore Workforce Skills: Demand & Gap Forecast

An empirical study that decodes Singapore's skills market landscape to identify structural skill shortages and forecast future workforce demand.

The **Singapore Workforce & Skills Demand Intelligence Dashboard** bridges these gaps by transforming raw posting and application behavior into actionable labor market intelligence for Manpower Policy Analysts (e.g., MOM, SSG, WSG) who require real-time labor market signals beyond delayed annual or quarterly surveys.

---

## Business Scenario

Singapore's rapidly evolving economic landscape, driven by digital transformation, green transitions, and demographic shifts, is changing job and workforce requirements. 

This dashboard identifies talent demand and skills gaps to:

* **Empower Singapore remain competitive in the global landscape by aligning workforce skills with emerging market opportunities**
  - Identify high-demand sectors and roles that align with Singapore's strategic economic priorities (e.g., tech, fintech, green energy)
  - Highlight emerging skill requirements before they become critical bottlenecks
  - Enable businesses to invest in upskilling initiatives that position Singapore as a talent hub in Asia

* **Strengthen Singapore's labour market uphold global standards through data-driven insights on skill requirements and compensation benchmarks**
  - Identify skill gaps that could hinder Singapore's ability to attract multinational talent and investment

* **Accelerate proactive workforce planning by identifying growth sectors and future skills demands**
  - Forecast talent shortages before they impact business operations
  - Guide educational institutions and training providers on priority skill development areas
  - Support policy makers in designing targeted workforce development programs that address real market needs

---

## Stakeholder

| Policymakers | Organization | Value |
|---|---|---|
| Manpower | MOM, SSG | Identification of shortage occupations to calibrate SkillsFuture training subsidies, adjust work pass frameworks, and target reskilling initiatives. |
| Investment & Trade | EDB & Ministry of Trade | Skills gap data attracts targeted FDI by demonstrating workforce readiness in high-value sectors (semiconductors, AI, green tech). |
| Investment & Trade | EDB & Ministry of Trade | Guides strategic investment sourcing—identifies which industries to prioritize based on talent availability and competitive advantage positioning. |

# Data Handling and Process
![Alt Text](Data_Pipeline.png)

# Team challenges and our learnings

## 1. Collaboration & Version Control
**The Challenge (Team Workflow):** As a team, coordinating our work using Git and GitHub within VS Code posed a steep learning curve. We frequently ran into issues with remote branches, keeping our local environments synced, and dealing with merge conflicts when multiple people edited the same files.

**The Learning:** We learned the importance of clear communication and version control hygiene. By the end of the project, we established a solid workflow—pulling the latest changes before starting, dividing work into separate branches, and communicating clearly before merging code.
# 2. Business Alignment & Scope Creep
**The Challenge (Staying Focused):** With over a million rows and everyone finding different interesting patterns during EDA, it was incredibly easy for us to experience scope creep and lose sight of the core objective.

**The Learning:** We learned to be ruthless as a team with our dashboard design. We had to constantly check in with each other and ask, "Does this metric actually help our target user make a decision?" This collaborative filtering kept our final product focused and actionable.
# 3. Resilience & Shared Problem-Solving
**The Challenge (The Unknowns):** Processing a massive, messy dataset meant we constantly ran into roadblocks, from memory bottlenecks to parsing nested JSON strings in the categories column.

**The Learning:** We learned that data projects require immense resilience. More importantly, we learned the value of leaning on each other’s strengths. When one of us got stuck on a Pandas error, another could provide a fresh set of eyes, teaching us that resourcefulness and team problem-solving are just as important as knowing the code.

## Our Next Steps
**Maintaining the "Business-First" Habit:** Because we practiced defining our specific business problem and target audience right at the start of this project, we experienced firsthand how crucial that first step is. We plan to keep this habit front and center for all future projects so we always have a clear "north star."

**Refining Team Workflows:** For future projects, we want to establish our GitHub branching strategy and data pipeline architecture before anyone writes a line of code, making collaboration even smoother.

**Knowledge Sharing:** Since we divided and conquered different parts of the project (e.g., one person on cleaning, one on the dashboard), our next step is to do a thorough code-review session with each other so everyone fully understands the entire technical pipeline.
