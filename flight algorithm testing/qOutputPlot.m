%% open qLog file from testing and rollOutput history && compare the vehicle roll with the commands from the q-matrix
clear variables;
close all;

qfile = 'qLog2.txt';
rollFile = 'rollOutput.txt';

rollTime = 247;%time of target detection, in seconds from start of rollFile. This is hardwired for the trial used.

Q = csvread(qfile,1,0);
R = dlmread(rollFile,'\t',1,0);
R(:,1) = R(:,1) - min(R(:,1));
R(:,1) = R(:,1)*.001;

[~,ix] = sort(R(:,1));
R = R(ix,:);

tfin = rollTime + max(Q(:,1));
tst = find(R(:,1) >= rollTime,1,'first');
tft = find(R(:,1) >= tfin,1,'first');

t = R(tst:tft,1) - rollTime;
phi = R(tst:tft,2);%in rads

figure;
subplot(2,3,[1 2 4 5])
plot(t(1:end-1),diff(phi*r2d));
hold on;
plot(Q(:,1),Q(:,8),'r--');
ylabel('\Delta\phi');
xlabel('t (sec)');
grid on;

subplot(2,3,3);
plot(Q(:,5),Q(:,6),'b-x');
xlabel('X (px)');
ylabel('Y (px)');
grid on;

subplot(2,3,6);
plot(t,phi*r2d);
hold on;
plot(Q(:,1),Q(:,7),'r--');
ylabel('\phi (deg)');
grid on;

set(gcf,'position',[125 575 1175 375]);