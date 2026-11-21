import time

import docker
from requests.exceptions import ReadTimeout


def test_infinite_loop_timeout():
    # prep the client and variables to create a container
    client= docker.from_env()
    image= "python:3.12-slim"
    code= "while True: pass"

    print("Spawning container with infinite loop...")
    # create the container
    container= client.containers.create(
        image=image,
        command=["python","-c", code],
        network_mode="none",
        read_only=True,
        mem_limit="128m",
        pids_limit=64,
        cap_drop=["ALL"],
        security_opt=["no-new-privileges"],
        tmpfs={"/tmp":"rw,noexec,nosuid,size=64m"},
        user="1000:1000"
    )

    # start the container and note it's id
    container.start()
    container_id= container.id[:12]
    print(f"Container started (ID: {container_id})")

    # make a note of start time 
    start_time= time.time()
    timed_out= False

    try:
        print("Waiting for container with 2s timeout...")
        container.wait(timeout=2.0)
    except (ReadTimeout, Exception):  # noqa: BLE001
        timed_out= True
        print("Timeout reached! Forcibly killing container...")
        container.kill()
        container.wait() # wait for daemon to kill the signal

    # note the time taken to complete this process 
    elapsed_time= time.time() - start_time
    print(f"Execution completed in {elapsed_time:.2f} seconds (Timed out: {timed_out})")

    # verify container is not active 
    running_containers= client.containers.list(filters={"id":container_id})
    assert len(running_containers) == 0, "Container is still running!"
    print("Verification passed: Container is completely gone from active list.")

    # remove container 
    container.remove()
    print("Container removed successfully")

if __name__=="__main__":
    test_infinite_loop_timeout()




    
