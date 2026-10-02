# Slipstream Oracle Website Design Plan
This Markdown file describes the design plan of Slip Stream Oracle website. This document clearly specifies the design ideas, related files and Metadata that should be on the website clearly with ease

## About the Website
This is a Formula 1 Styled and related website used to display the predicted values of the podium provided by the ML Model. Rather than the specified tasks this website has some stylings that is simply re-imagined. This website should be styled with latest UI techniques yet light weight. I prefer using only HTML, JS and CSS. Avoid TypeScript. That's heavy

## Files and other contents
The Background video to play in the Home Page, Headshots and other files are located in the assets folder. You can take a look

## Website Components and their Details
The website must contain the Tab based structure. The Logo of this website is present in `assets/Slipstream_Oracle.png` should be always displayed at the top right given the situation, whatever tab is open, whether it's home, models or whatever. The Components it must posses are:
- Home
- Drivers
- Models
- DataHub
- About

### Home
This is the Home page of this website. Here are the design and how to look of home page:
- In the Top left below the tab that contains the Home, Drivers etc, I wish to have the F1 logo, located in `assets/f1_logo.png` have the sizes accordingly so thatit looks weighted, notable and neat
- This page should play a background video located in `assets/bg_f1.mp4` without audio. Make it suffeciently blur so that the texts on the foreground is clearly visible
- Next below the F1 logo, have a nice, driver signed style, clearly visible weighted Heading of the text "Slipstream Oracle", like Slipstream like a signed one by human and Oracle text neatly written down to it
- And a short description about this (Babe! Enchance this!)

### Drivers
Next is the drivers tab! It contains the Driver details of this season
- This page should have cards for each driver
- Each card should display the contents and metadata mentioned in `drivers.json`
- The Headshot images should be rendered such that, it's not fully visible and upto Hip of the drivers are visible

### Models
This Tab trigger opens up. Then shows:
- Simply Cards that has Model used by Slipstream
- For now, just add a simple card of RandomForest, because it's the one currently used by Slipstream Oracle

### DataHub
This is tab is the core, it actually contains:
- The cards of the GP should be displayed with the name of it
- The extra card should be dynamically created by checking for the folder names in the specified location. The folder names would be "Monaco_Grand_Prix". It shoud remove the underscores and neatly display! For now, Let this be a sample!
- The card should be created only when `Final_Data.csv` file is present even if the GP foldedr exists
- This webpage will be in website folder. The data is actually present in `../predictions/2026/GP_NAME/Final_Data.csv`
- Ask Antigravity to comment this part! After testing I will uncomment it!

### About
It contains the copyright and about instruction (Babe! Enchance this!)