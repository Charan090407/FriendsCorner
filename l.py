class Node:
    def __init__(self, data=None, next=None):
        self.data = data
        self.next = next

class LinkedList:
    def __init__(self):
        self.head = None
    
    def add_on_begining(self,data):
        new_node = Node(data)
        new_node.next = self.head
        self.head = new_node

    def add_on_end(self,data): 
        if self.head is None:
            self.head = Node(data)
            return
        
        itr = self.head
        while itr.next:
            itr = itr.next
        itr.next = Node(data)

    def printlist(self):
        current_node = self.head
        if current_node is None:
            print("List is empty")
        while current_node:
            print(current_node.data,end=" -> ")
            current_node = current_node.next
    
    

llist  = LinkedList()
llist.add_on_end(10)
llist.add_on_end(11)
llist.add_on_end(12)
llist.printlist()


  

    