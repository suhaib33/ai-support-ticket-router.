"""Generates the messy sample inbox + ground-truth labels. Run once."""
import pandas as pd
rows = [
(1,"2026-11-24 09:01","rahul.m@gmail.com","Bulk order","Hi, I want a bulk discount for 200 units of the X200 laptop. Who do I talk to?","Sales","Sales","Medium"),
(2,"2026-11-24 09:04","anita.k@yahoo.com","","The blender I received stopped working after 2 days. Order 4521. pls help","Product","Product","Medium"),
(3,"2026-11-24 09:07","vikram.s@outlook.com","Invoice","Where can I download my invoice for order 4533?","Billing","Finance","Low"),
(4,"2026-11-24 09:10","neha.p@gmail.com","Question","Does the X200 laptop support 32GB RAM?","Product","Product","Low"),
(5,"2026-11-24 09:12","sameer.j@gmail.com","URGENT!!!","I was charged twice for the same order 4540!! Card ending 4417. Fix this NOW. My number is 9876543210","Billing","Finance","High"),
(6,"2026-11-24 09:15","corp.buyer@acmeltd.com","Enterprise plan demo","Can I get a demo of your enterprise plan? We are a team of 80.","Sales","Sales","Medium"),
(7,"2026-11-24 09:18","priya.d@gmail.com","","Your website keeps crashing when I try to log in. Tried 3 browsers.","IT","IT","High"),
(8,"2026-11-24 09:20","guest123@gmail.com","Store timing","Is the store open on Sunday?","General","Support","Low"),
(9,"2026-11-24 09:22","seo.deals@rankfast.biz","Boost your Google ranking!!","Dear Sir, we can put your website on page 1 of Google in 7 days. Reply now for 50% OFF.","Spam","Spam Review","Low"),
(10,"2026-11-24 09:25","hr.jobs@gmail.com","Application for Data Analyst","Respected sir, I am writing to apply for the post of Data Analyst. Please find my CV attached.","Spam","Spam Review","Low"),
(11,"2026-11-24 09:27","auto@vendor.com","Automatic reply: Out of office","I am out of office until Monday with limited access to email.","Spam","Spam Review","Low"),
(12,"2026-11-24 09:30","tarun.b@gmail.com","Where is my parcel","Where is my Amazon parcel? It was supposed to arrive yesterday.","Spam","Spam Review","Low"),
(13,"2026-11-24 09:33","deepa.r@gmail.com","Broken + bulk","My blender broke, and I also want a bulk quote for 50 more of the newer model.","Product+Sales","Product|Sales","Medium"),
(14,"2026-11-24 09:36","imran.a@gmail.com","","mera order abhi tak nahi aaya, order 4552 ka status batao","General","Support","Medium"),
(15,"2026-11-24 09:38","  Rahul.M@gmail.com ","Bulk order","Hi, I want a bulk discount for 200 units of the X200 laptop.   Who do I talk to?","Sales","Sales","Medium"),
(16,"2026-11-24 09:41","kavita.n@gmail.com","Refund","I returned my headphones 10 days ago and still no refund. Please check, order 4560. Call me on +91 98450 11223.","Billing","Finance","Medium"),
(17,"2026-11-24 09:44","long.writer@gmail.com","Hello","Hello team, hope you are doing well. I have been a customer for 6 years and my family also buys from you. Last month we moved houses, then my father was unwell, then the festival season began, and I could not check things. Anyway, I ordered a washing machine WM-77 and the display shows error E4 and it will not start. Can you tell me what E4 means and how to fix it?","Product","Product","Medium"),
(18,"2026-11-24 09:47","pooja.t@gmail.com","Payment failed","Payment page shows error 500 when I click pay. Money not deducted but I cannot checkout.","IT","IT","High"),
(19,"2026-11-24 09:50","ravi.g@gmail.com","return policy","what is your return policy for electronics?","General","Support","Low"),
(20,"2026-11-24 09:52","vendor.x@gmail.com","partnership","We would like to discuss a reseller partnership for your product line in Maharashtra.","Sales","Sales","Medium"),
(21,"2026-11-24 09:55","anita.k@yahoo.com","","The blender I received stopped working after 2 days. Order 4521. pls help","Product","Product","Medium"),
(22,"2026-11-24 09:58","sunil.v@gmail.com","???","","Unclear","Needs Review","Low"),
(23,"2026-11-24 10:01","maya.s@gmail.com","Hi","pls help my ordr not here","General","Support","Medium"),
(24,"2026-11-24 10:04","lottery@winner-now.xyz","YOU WON $1,000,000","Click this link to claim your prize now!!!","Spam","Spam Review","Low"),
]
cols = ["ID","Received At","Customer Email","Subject","Message","category","team","priority"]
df = pd.DataFrame(rows, columns=cols)
df[cols[:5]].to_excel("data/support_inbox.xlsx", index=False, sheet_name="Inbox")
df.rename(columns={"ID":"id"})[["id","category","team","priority"]].to_csv("data/expected_labels.csv", index=False)
print(len(df), "rows written")
