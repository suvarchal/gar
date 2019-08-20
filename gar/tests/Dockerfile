FROM ubuntu:18.04
COPY echo.sh /usr/bin/gar

# create two groups 
RUN addgroup group1 
RUN addgroup group2 

# add 5 users within different groups
 
# user1 within one group1, as primary group
#RUN adduser --system --ingroup group1 user1 
RUN useradd -m -g group1 user1

# user1 within just one group2
RUN useradd -m -g group2 user2

# user3 within two groups: group1 as primary, group2 as secondary
RUN useradd -m -g group1 -G group2 user3

# user4 within two groups: group2 as primary, group2 as secondary
RUN useradd -m -g group2 -G group1 user4

# user5 create user like system user with defaults of username group &
# group1, group2 as secondary groups.
RUN useradd -r -m -G group1,group2 user5


# create temporary files
USER user1
RUN cd /home/user1 && \
    fallocate -l 12M user1_file1 && \
    fallocate -l 24M user1_file2  

USER user2
RUN cd /home/user2 && \
    fallocate -l 12M user2_file1 && \
    fallocate -l 24M user2_file2  

USER user3
RUN cd /home/user3 && \
    fallocate -l 12M user3_file1 && \
    fallocate -l 24M user3_file2  

USER user4
RUN cd /home/user4 && \
    fallocate -l 12M user4_file1 && \
    fallocate -l 24M user4_file2  

USER user5
RUN cd /home/user5 && \
    fallocate -l 12M user5_file1 && \
    fallocate -l 24M user5_file2  

USER root

CMD ["/usr/bin/gar"]
