# Mini_Amazon_Proj
To see detailed functions of this project, please see [project.pdf](https://github.com/ys270/Mini_Amazon_Proj/blob/master/project.pdf).
The add on functions are all in [differentiation.txt](https://github.com/ys270/Mini_Amazon_Proj/blob/master/differentiation.txt).

To mimic the whole process of purchasing items in the world, this project need to cooperate with the UPS side.
The UPS first connect to the world and send the world id to Amazon, Amazon then generate a Aconnect command to the world.
After all the connections are done, we can purchase things in the front end and the backend will handle all the requests 
and push things forward.
### Run frontend
```
python3 manage.py runserver 0:8000
```
Then, go to vcm-xxxxx.vm.duke.edu:8000/amazon
### Run backend
```
python3 backend.py
```

