# Celery

Celery is an open-source, distributed task queue system that enables you to run time-consuming Python functions in the
background as asynchronous tasks. It allows your application to perform complex computations or handle heavy workloads
without blocking the main execution thread, thereby improving performance and user experience.

When combined with Redis, an in-memory data structure store used as a message broker, Celery can efficiently manage and
distribute tasks across multiple workers or machines.

### How Celery Works with Redis

1. Task Definition: You define tasks in your application using the @celery.task decorator. These tasks are regular
   Python functions that you want to run asynchronously.
2. Task Invocation: When your application needs to execute a task, it sends a message to the Celery task queue instead
   of executing the function immediately.
3. Message Broker (Redis): Redis acts as the intermediary that holds the task messages. It queues the tasks and ensures
   they are delivered to the workers.
4. Workers: Celery workers are processes that listen to the Redis queue. They pick up tasks, execute them, and can store
   the results if needed.
5. Result Backend (Optional): If you need to retrieve the results of a task, Celery can store them using Redis or
   another backend so your application can access them later.

### Benefits

- Asynchronous Execution: Offload long-running tasks to the background, keeping the main application responsive.
- Scalability: Easily add more workers to handle increased load without changing your application code.
- Reliability: Tasks are stored in Redis until they are successfully executed, ensuring no loss of tasks.
- Scheduling: Support for executing tasks at specific times or intervals.
