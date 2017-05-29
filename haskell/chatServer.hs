-- From https://wiki.haskell.org/Implement_a_chat_server

-- in Main.hs
module Main where
 
import Network.Socket (socket, Socket, SockAddr(..), Family(..), SocketType(..), 
    setSocketOption, bind, SocketOption(..), listen, iNADDR_ANY, accept,
    socketToHandle)
import System.IO -- (IOMode(..), BufferMode(..), hSetBuffering)
import Control.Exception
import Control.Concurrent (Chan, readChan, newChan, forkIO, 
                           writeChan, dupChan, killThread)
-- import Control.Concurrent.Chan ()
import Control.Monad (liftM, when)
import Control.Monad.Fix (fix)


anInternetSocket :: IO Socket
anInternetSocket = socket AF_INET Stream 0
 
main :: IO ()
main = do
    mainSocket <- anInternetSocket 
    setSocketOption mainSocket ReuseAddr 1
    bind mainSocket (SockAddrInet 4242 iNADDR_ANY)
    listen mainSocket 2
    chan <- newChan
    forkIO $ fix $ \loop -> do
       (_, msg) <- readChan chan
       loop
    mainLoop mainSocket chan 0

type Message = (Int, String)

mainLoop :: Socket -> Chan Message -> Int -> IO ()
mainLoop sock chan msgNum = do
    conn <- accept sock
    forkIO (runConn conn chan msgNum)
    mainLoop sock chan $! msgNum + 1

unNamedFunction :: Eq a => Chan (a, String) -> a -> Handle -> IO b -> IO b
unNamedFunction commLine msgNum hdl x = do
   (nextNum, line) <- readChan commLine
   when (msgNum /= nextNum) $ hPutStrLn hdl line
   x
 
runConn :: (Socket, SockAddr) -> Chan Message -> Int -> IO ()
runConn (sock, _) chan msgNum = do
    let broadcast msg = writeChan chan (msgNum, msg)
    hdl <- socketToHandle sock ReadWriteMode
    hSetBuffering hdl NoBuffering

    hPutStrLn hdl "Hi, what's your name?"
    name <- liftM init (hGetLine hdl)
    broadcast ("--> " ++ name ++" entered chat.")
    hPutStrLn hdl ("Welcome, " ++ name ++ "!")

    commLine <- dupChan chan

    -- fork off a thread for reading from the duplicated channel
    reader <- forkIO $ fix $ (unNamedFunction commLine msgNum hdl)

    handle (\(SomeException _) -> return ()) $ fix $ \loop -> do
        line <- liftM init (hGetLine hdl)
        case line of
             -- If an exception is caught, send a message and break the loop
             "quit" -> hPutStrLn hdl "Bye!"
             -- else, continue looping.
             _      -> broadcast (name ++ ": " ++ line) >> loop
 
    killThread reader                      -- kill after the loop ends
    broadcast ("<-- " ++ name ++ " left.") -- make a final broadcast
    hClose hdl                             -- close the handle
