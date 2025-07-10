## README

Usecase:

You want to be able to add people to a discord server and to automatically have them kicked after a specified amount of time. Additionally, you can intervene manually to prevent this process.

Technical detail below

# What it DOES

- adds the role named "Visa" to people who join the server while its online
- adds the role named "Visa" to people who joined the server while it was online
- kicks people with the role name "Visa" from the server after a specified amount of time (does so by checking when it comes online and every 5 minutes)
- !visa will give the amount of time left the person who says it has left before autokick
- !visa @member will be the amount of time left individual in the at has left before autokick
- if !visa is used on someone without the "Visa" role it will state that that person is a permanent member of the server

# What it DOESN'T

- create a role called "Visa"
- manage perms of "Visa"

# temp
Making a temporary change to test something