# Job Queue Design Document

## Purpose
The job queue takes in jobs (which are ml tasks (training/deployment)) and holds them in the queue.
Our compute servers (like vaughan, or maybe something on NERSC) will read jobs from the queue, and launch the appropriate container to run the job.

Several problems have emerged.

### Managing Connections
The job queue relies on a heartbeat to maintain a connection to producers (like my dash front end) and consumers (like my compute server). So if you have a long running task (like training an ml model), then the heartbeat will be blocked, and the connection will be disconnected.

The way rabbitmq is supposed to be used is one connection, many channels (a channel is like a seperate queue). The connections are supposed to be long lived and passed around, as it is slow to establish a connection, but cheap to start a channel.

The problem is that I am not skilled enough to create a robust connection handler. As well, making this work with a dash app, which is stateless, isn't so obvious to me. Especially in a multipage app-- do you initialize the connection on the mother-app (the app which calls the smaller single page applications (like training, or thumbnail_tab.py))? Where do you store the connection then, if the app is stateless? How do you pass the connection to the other, single page apps? If one of the
single page apps breaks the connection, how do you re-initialize it?
These are not insurmountable challenges, but they will need to be answered to proceed in the 'official' way.

What I have done is to have a connection established every time a job is passed into the queue. This is more robust (you are explicity opening and closing connections on the single page application, and everything is contained within that namespace (you don't have to worry about communicating to other 'apps' within the mother-application).)

## Heartbeat Problem

Rabbitmq uses a heartbeat (a simple ping that says "Im still alive"), to keep connections open (both the producer and consumer). Unfortunately, if you have a long running task, then the hearbeat will be blocked and the connection will be dropped. A long running task like... say... training a ml model? 

The official guideline for this is to use threads-- you launch your long running task on a thread, and then the heartbeat can still beat on the main thread. 

Digression on threads (Could be incorrect):

I don't understand threads. They are a lightweight way of using concurrency in your program, but because python has a global interpreter lock, it isn't true concurrency, but fake? Anyway, the way you use them is like so:

```
thread1 =Threading.Thread(func_to_launch_on_new_thread, args, kw_args)
thread1.start()
```
So now the thread is off and running, and your main program can continue on its merry way.
But if you want to get anything from your thread, you need to block on it (wait for it to finish)

```
thread1 =Threading.Thread(func_to_launch_on_new_thread, args, kw_args)
thread1.start()
# more things you want to do in main
thread1.join() # wait for thread1 to finish and get values from it
```
I think usually the paradigm is you have some task you can do in parallel, then you launch a lot of threads to
do that task, they work on some subset of the original task and then report back. Like:
```
               |- thread1-|
main program ->|- thread2-|-> main program
               |- thread3-|
        thread.start()  thread.join()
------time-------------------------->
```
so, thread.join is blocking-- the program won't advance until all the threads finish and 'join' back together. 
We don't want to do this. We explicitly don't want any blocking code, so our heartbeat can go out.
Instead of using threads, I'm using multiprocesses. So the code will get launched on a seperate CPU, and we'll get
true concurrency. 

So, it looks like:
```
main_program(heartbeat) -> | -> main_program (heartbeat) 
                           | -> (ml container (on diff cpu))
```
So how do we get the ml container to communicate the following:
1. it has started (nice to know it actually launched)
2. it has finished (or broke)
3. Any log files

I can think of two ways of doing this:
1. communicate through files. We are in a sandboxed folder, so we could just save log files and the model file to the sandboxed directory. When the model file is saved, that is the signal that we are done and the model is trained.

This has the disadvantage of not really using the good properties of a job queue. Say the container gets shut down, or can't finish? Because we haven't included the job queue in the loop here, it would have no way of knowing and being able to relaunch the job on failure.

2. Communicate through the job queue.
I see two options, both have pros and cons:
![job_finished_choice](https://user-images.githubusercontent.com/990372/121726353-4881a980-ca9f-11eb-8cfc-3d68fe4afe88.png)




## Log
