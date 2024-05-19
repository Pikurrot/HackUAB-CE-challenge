![image](https://github.com/Pikurrot/HackUAB-CE-challenge/blob/main/images/Caixa%20Enginyers.png)
# HackUAB Caixa d'Enginyers Challenge
Project for the Caixa d'Enginyers challenge of "UAB the Hack" hackathon 2024 

<p>This project we have develop is a way to solve **Caixa Enginyers**'s problem
</p>

### The Problem
<p>
The proposed problem consists on creating a software solution for calculating the<br>
most optimal path one worker should take to cover a vast region of space whilst  <br>
visitng them all. While doing this we need to consider the time it takes for the <br>
worker to get from one place to another and how much time should it spend there  <br>
to take into account it's schedule.
</p>

---
<p>
El problema propuesto consiste en crear una solucion de software para calcular   <br>
las rutas mas optimas para que un trabajador cubra el area una basta region pero <br>
visitando todos los lugares. Para hacer esto tenemos que considerar el tiempo que<br>
tarda el trabajador en ir entre lugares y el queda de pasar en cada lugar para   <br>
tener en cuenta su horario.
</p>

### Our Solution
<p>
To tackle the problem we first started by developing a graph of the given        <br>
regions. We did this by searching for api's that would help us determine the     <br>
distance between cities. And also to determine in real time how much traffic is  <br>
on the roads to get a better estimation.<br>
</p>

---
<p>
Para empezar a estudiar este problema hemos construido un grafo con datos sacados<br>
de varias api para tener las distancias entre ciudades. Tambien hemos sido       <br>
capaces mediante otra api de tener la densidad de trafico actual en las          <br>
carreteras en timepo real para asi poder calcular mas percisamente el tiempo     <br>
entre dos lugares.
</p>

![image](https://github.com/Pikurrot/HackUAB-CE-challenge/blob/main/images/Graph%20without%20paths.png)

<p>
After that we created an algorithm capable of finding the desired path of the    <br>
worker given the data we are interested in, this are: starting point, schedule   <br>
and the places where it needs to be.
</p>

---
<p>
Despues de eso creamos el algoritmo que busca los caminos para el trabajador dado<br> 
los datos que utilizamos: punto de inicio, horario y el mapa. 
</p>

![image](https://github.com/Pikurrot/HackUAB-CE-challenge/blob/main/images/Graph%20with%20paths.png)

<p>
Finally we created an Android app made on Flutter that would allow the           <br>
hypothetical worker to follow the path to it's destination.
</p>

---
<p>
Finalmente hemos creado una applicaion de Android con Flutter que enseña la ruta<br>
que seguiria un hipotetico trabajador para llegar a su destino.
</p>

![image](https://github.com/Pikurrot/HackUAB-CE-challenge/blob/main/images/Map_page.png)
![image](https://github.com/Pikurrot/HackUAB-CE-challenge/blob/main/images/Map_page_2.png)


