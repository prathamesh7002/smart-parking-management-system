#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
using namespace std;

const int MAX_SLOTS = 20;
const int TABLE_SIZE = 11;

struct Vehicle
{
    string number, owner, type;
    int slot = -1;
};

// array- parking slot
string slots[MAX_SLOTS];

// Queue(fifo)-linked list with front and rear end

struct QueueNode
{
    Vehicle v;
    QueueNode *next;
};

struct WatingQueue
{
    QueueNode *front = nullptr;
    QueueNode *rear = nullptr;

    int size = 0;
    // return true is queue is empty
    bool isEmpty()
    {
        return size == 0;
    }
    // adding the vehical to the wating list in the back
    void enqueue(Vehicle v)
    {
        QueueNode *n = new QueueNode{v, nullptr};

        if (rear)
        {
            rear->next = n;
        }
        else
        {
            front = n;
        }
        rear = n;
        size++;
    }
    // removing the vehical from the front

    Vehicle dequeue()
    {
        QueueNode *n = front;
        Vehicle v = n->v;
        front = n->next;
        if (!front)
            rear = nullptr;
        delete n;
        size--;
        return v;
    }
    // to check the given number is in the wating queue or not
    bool contains(const string &no)
    {
        for (QueueNode *p = front; p; p = p->next)
        {
            if (p->v.number == no)
            {
                return true;
            }
        }
        return false;
    }

    void clear()
    {
        while (!isEmpty())
        {
            dequeue();
        }
    }
};
// stack(lifo)-array + top index
//      A slot is pushed only when it becomes free, and the array is scanned
//      only when the stack is empty, so the stack can never overflow.

struct VacatedStack
{
    int data[MAX_SLOTS];
    int top = -1;

    bool isEmpty()
    {
        return top == -1;
    }
    void push(int s)
    {
        data[++top] = s;
    }
    int pop()
    {
        return data[top--];
    }
    void clear()
    {
        top = -1;
    }
};

// HASH TABLE - separate chaining (key = vehicle number)
// hash(key) = (h * 31 + character )% TABLE_SIZE

struct HashNode
{
    Vehicle v;
    HashNode *next;
};

struct HashTable
{
    HashNode *bucket[TABLE_SIZE] = {};

    int hashOf(string key)
    {
        int h = 0;
        for (char c : key)
        {
            h = (h * 31 + (unsigned char)c) % TABLE_SIZE;
        }
        return h;
    }
    void insert(Vehicle v)
    {
        int b = hashOf(v.number);
        bucket[b] = new HashNode{v, bucket[b]};
    }

    Vehicle *search(string key)
    {
        for (HashNode *p = bucket[hashOf(key)]; p; p=p->next)
        {
            if (p->v.number == key)
            {
                return &p->v;
            }
        }
        return nullptr;
    }

    void remove(string key)
    {
        int b = hashOf(key);
        HashNode *prev = nullptr;
        for (HashNode *p = bucket[b]; p; prev = p, p = p->next)
        {
            if (p->v.number == key)
            {
                if (prev)
                    prev->next = p->next;
                else
                    bucket[b] = p->next;
                delete p;
                return;
            }
        }
    }

    void clear()
    {
        for (int b = 0; b < TABLE_SIZE; b++)
        {
            while (bucket[b])
                remove(bucket[b]->v.number);
        }
    }
};
// need tosend to GUI
WatingQueue waiting;
VacatedStack vacated;
HashTable table;

bool ok = true;
string message;
string hlSlot;     // slot to highlight
int hlBucket = -1; // bucket to highlight

string slotName(int i)
{
    return "P" + string(i < 9 ? "0" : "") + to_string(i + 1);
}
string toUpper(string s)
{
    for (char &c : s)
    {
        c = toupper((unsigned char)c);
    }
    return s;
}
void fail(string text)
{
    ok = false;
    message = text;
}

// main operation
// Pick a slot: use the stack first (most recently vacated), else scan the array.
int findFreeSolt()
{
    if (!vacated.isEmpty())
        return vacated.pop();

    for (int i = 0; i < MAX_SLOTS; i++)
    {
        if (slots[i].empty())
            return i;
    }
    return -1; // parking is full
}

void parkVehicle(Vehicle v, int i)
{
    v.slot = i;
    slots[i] = v.number; // array update
    table.insert(v);     // hash table insert
    hlSlot = slotName(i);
    hlBucket = table.hashOf(v.number);
}

void addVehicle(string no, string owner, string type)
{
    no = toUpper(no);
    if (no.empty() || owner.empty())
    {
        fail("vehicle number and owner name are required");
        return;
    }
    if (type.empty())
        type = "Car";
    hlBucket = table.hashOf(no);

    if (table.search(no) || waiting.contains(no))
    {
        fail(no + "is already in the system");
        return;
    }

    Vehicle v;
    v.number = no;
    v.owner = owner;
    v.type = type;

    int i = findFreeSolt();
    if (i >= 0)
    {
        parkVehicle(v, i);
        message = no + "parked at" + slotName(i);
    }
    else
    {
        waiting.enqueue(v); // parking full
        hlBucket = -1;
        message = "parking full." + no + "added to the wating queue(position " + to_string(waiting.size) + ")";
    }
}
void exitVehicle(string no)
{
    no = toUpper(no);
    hlBucket = table.hashOf(no);
    Vehicle *p = table.search(no); // hash table search
    if (!p)
    {
        fail(no + " not found");
        return;
    }

    int i = p->slot;
    table.remove(no); // hash table delete
    slots[i] = "";    // array upadte
    vacated.push(i);  // stack push
    hlSlot = slotName(i);
    message = no + "exited from " + slotName(i);

    if (!waiting.isEmpty())
    {
        Vehicle w = waiting.dequeue();
        int j = findFreeSolt();
        parkVehicle(w, j);
        message += ". waiting vehicle " + w.number + "moved" + slotName(j);
    }
}

void searchVehicle(string no)
{
    no = toUpper(no);
    hlBucket = table.hashOf(no);
    Vehicle *p = table.search(no);
    if (p)
    {
        hlSlot = slotName(p->slot);
        message = no + " | " + p->owner + " | " + p->type + " | slot " + hlSlot;
    }
    else if (waiting.contains(no))
    {
        message = no + " is waiting in the queue";
    }
    fail(no + " not found");
}

// send the ans to gui
void printAnswer()
{
    cout << (ok ? "OK|" : "ERR|") << message << "\n";
    cout << "HIGHLIGHT|" << hlSlot << "|" << hlBucket << "\n";

    for (int i = 0; i < MAX_SLOTS; i++)
        cout << "SLOT|" << slotName(i) << "|" << slots[i] << "\n";

    for (QueueNode *p = waiting.front; p; p = p->next)
        cout << "QUEUE|" << p->v.number << "|" << p->v.owner << "|" << p->v.type << "\n";

    for (int i = vacated.top; i >= 0; i--) // top first
        cout << "STACK|" << slotName(vacated.data[i]) << "\n";

    for (int b = 0; b < TABLE_SIZE; b++)
    {
        cout << "BUCKET|" << b;
        for (HashNode *p = table.bucket[b]; p; p = p->next)
            cout << "|" << p->v.number << "," << slotName(p->v.slot);
        cout << "\n";
    }
    cout << "END" << endl; // endl also flushes the output
}
// read commands from the gui

vector<string> split(string line)
{
    vector<string> parts;
    stringstream ss(line);
    string item;
    while (getline(ss, item, '|'))
    {
        parts.push_back(item);
    }
    while (parts.size() < 4)
        parts.push_back("");
    return parts;
}

int main()
{
    string line;
    while (getline(cin, line))
    {
        vector<string> p = split(line); // p[0]=command  p[1]=number  p[2]=owner  p[3]=type

        ok = true;
        message = "Status refreshed";
        hlSlot = "";
        hlBucket = -1;

        if (p[0] == "add")
            addVehicle(p[1], p[2], p[3]);
        else if (p[0] == "exit")
            exitVehicle(p[1]);
        else if (p[0] == "search")
            searchVehicle(p[1]);
        else if (p[0] == "reset")
        {
            for (int i = 0; i < MAX_SLOTS; i++)
                slots[i] = "";
            waiting.clear();
            vacated.clear();
            table.clear();
            message = "System reset";
        }
        else if (p[0] == "quit")
            break;

        printAnswer();
    }
    return 0;
}